from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional
import unicodedata

import requests


FINAL_STATUSES = {"FINISHED", "AWARDED"}


@dataclass
class ExternalMatchResult:
    source_id: str
    utc_kickoff: datetime
    match_date: date
    home_name: str
    away_name: str
    home_tla: str
    away_tla: str
    home_goals: int
    away_goals: int
    classified_team: Optional[str]


def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    decomposed = unicodedata.normalize("NFD", value.strip().lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _parse_utc(value: str) -> datetime:
    # football-data returns RFC3339 with trailing Z
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def fetch_finished_matches_football_data(
    api_key: str,
    date_from: date,
    date_to: date,
    base_url: str = "https://api.football-data.org/v4",
    timeout: int = 25,
) -> List[ExternalMatchResult]:
    url = f"{base_url.rstrip('/')}/competitions/WC/matches"
    headers = {"X-Auth-Token": api_key}
    params = {
        "dateFrom": date_from.isoformat(),
        "dateTo": date_to.isoformat(),
    }

    response = requests.get(url, headers=headers, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    results: List[ExternalMatchResult] = []
    for match in payload.get("matches", []):
        status = (match.get("status") or "").upper()
        if status not in FINAL_STATUSES:
            continue

        score = match.get("score") or {}
        full_time = score.get("fullTime") or {}
        home_goals = full_time.get("home")
        away_goals = full_time.get("away")
        if home_goals is None or away_goals is None:
            continue

        home_team = match.get("homeTeam") or {}
        away_team = match.get("awayTeam") or {}
        home_name = home_team.get("name") or ""
        away_name = away_team.get("name") or ""
        home_tla = (home_team.get("tla") or "").upper()
        away_tla = (away_team.get("tla") or "").upper()

        winner = (score.get("winner") or "").upper()
        classified_team = None
        if winner == "HOME_TEAM":
            classified_team = home_name
        elif winner == "AWAY_TEAM":
            classified_team = away_name

        kickoff_utc = _parse_utc(match.get("utcDate"))
        results.append(
            ExternalMatchResult(
                source_id=str(match.get("id")),
                utc_kickoff=kickoff_utc,
                match_date=kickoff_utc.date(),
                home_name=home_name,
                away_name=away_name,
                home_tla=home_tla,
                away_tla=away_tla,
                home_goals=int(home_goals),
                away_goals=int(away_goals),
                classified_team=classified_team,
            )
        )

    return results


def _find_internal_match(external: ExternalMatchResult, internal_matches: List) -> Optional[object]:
    window_start = external.match_date - timedelta(days=1)
    window_end = external.match_date + timedelta(days=1)
    in_window = [m for m in internal_matches if window_start <= m.data_jogo <= window_end]

    # Prefer FIFA code matching if available.
    for match in in_window:
        if (match.sigla_time_a or "").upper() == external.home_tla and (match.sigla_time_b or "").upper() == external.away_tla:
            return match

    # Fallback to name matching.
    ext_home = _normalize_text(external.home_name)
    ext_away = _normalize_text(external.away_name)
    for match in in_window:
        if _normalize_text(match.time_a) == ext_home and _normalize_text(match.time_b) == ext_away:
            return match

    return None


def sync_finished_results_football_data(
    db,
    Jogo,
    Resultado,
    Palpite,
    Pontuacao,
    calcular_pontuacao_jogo,
    *,
    api_key: str,
    base_url: str,
    days_back: int,
    days_forward: int,
    launched_by: str,
) -> Dict[str, object]:
    today = date.today()
    date_from = today - timedelta(days=max(days_back, 0))
    date_to = today + timedelta(days=max(days_forward, 0))

    external_results = fetch_finished_matches_football_data(
        api_key=api_key,
        date_from=date_from,
        date_to=date_to,
        base_url=base_url,
    )

    internal_matches = (
        Jogo.query
        .filter(Jogo.data_jogo >= date_from - timedelta(days=1))
        .filter(Jogo.data_jogo <= date_to + timedelta(days=1))
        .all()
    )

    created = 0
    updated = 0
    unchanged = 0
    unmatched: List[str] = []
    recalc_matches = []

    for external in external_results:
        jogo = _find_internal_match(external, internal_matches)
        if not jogo:
            unmatched.append(
                f"{external.match_date.isoformat()} {external.home_tla} x {external.away_tla}"
            )
            continue

        classificado = None
        if external.classified_team:
            # Keep internal naming where possible.
            if external.home_goals > external.away_goals:
                classificado = jogo.time_a
            elif external.away_goals > external.home_goals:
                classificado = jogo.time_b
            else:
                if _normalize_text(external.classified_team) == _normalize_text(external.home_name):
                    classificado = jogo.time_a
                elif _normalize_text(external.classified_team) == _normalize_text(external.away_name):
                    classificado = jogo.time_b

        result = Resultado.query.filter_by(jogo_id=jogo.id).first()
        if not result:
            result = Resultado(
                jogo_id=jogo.id,
                gols_a=external.home_goals,
                gols_b=external.away_goals,
                classificado=classificado,
                resultado_lancado=True,
                data_lancamento=datetime.utcnow(),
                usuario_lancamento=launched_by,
            )
            db.session.add(result)
            jogo.status = "Resultado Lançado"
            created += 1
            recalc_matches.append(jogo)
            continue

        changed = any(
            [
                result.gols_a != external.home_goals,
                result.gols_b != external.away_goals,
                (result.classificado or "") != (classificado or ""),
            ]
        )

        if not changed:
            unchanged += 1
            continue

        result.gols_a = external.home_goals
        result.gols_b = external.away_goals
        result.classificado = classificado
        result.resultado_lancado = True
        result.data_lancamento = datetime.utcnow()
        result.usuario_lancamento = launched_by
        result.updated_at = datetime.utcnow()
        jogo.status = "Resultado Lançado"
        updated += 1
        recalc_matches.append(jogo)

    db.session.flush()
    for jogo in recalc_matches:
        calcular_pontuacao_jogo(db, Palpite, Pontuacao, Resultado, jogo)

    db.session.commit()

    return {
        "date_from": date_from.isoformat(),
        "date_to": date_to.isoformat(),
        "fetched": len(external_results),
        "created": created,
        "updated": updated,
        "unchanged": unchanged,
        "unmatched": unmatched,
        "recalculated": len(recalc_matches),
    }
