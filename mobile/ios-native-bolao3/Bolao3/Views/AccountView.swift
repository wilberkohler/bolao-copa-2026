import SwiftUI
import UIKit

struct AccountView: View {
    @EnvironmentObject private var appState: AppState
    @State private var privateConfig: PrivateGroupConfigResponse?
    @State private var isLoadingConfig = false
    @State private var localMessage: String?
    @State private var showingDeleteSheet = false

    private let inviteURL = URL(string: "https://bolao2026-9jgh.onrender.com/registro")!
    private let privateGroupURL = URL(string: "https://bolao2026-9jgh.onrender.com/grupo-privado")!

    private var inviteText: String {
        "Convide um amigo para participar:\n\(inviteURL.absoluteString)"
    }

    var body: some View {
        NavigationStack {
            List {
                if let user = appState.user {
                    Section("Conta") {
                        VStack(alignment: .leading, spacing: 4) {
                            Text(user.nome)
                                .font(.headline)
                            Text(user.email)
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                            if let apelido = user.apelido, !apelido.isEmpty {
                                Text("Apelido: \(apelido)")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }

                Section("Convite") {
                    ShareLink(item: inviteText) {
                        Label("Convidar amigo", systemImage: "square.and.arrow.up")
                    }

                    Button {
                        UIPasteboard.general.string = inviteText
                        localMessage = "Convite copiado."
                    } label: {
                        Label("Copiar convite", systemImage: "link")
                    }
                } footer: {
                    Text(inviteURL.absoluteString)
                }

                Section("Grupo privado") {
                    if isLoadingConfig {
                        ProgressView("Carregando informacoes...")
                    } else if let privateConfig {
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Crie um grupo privado para administrar seus participantes.")
                                .font(.subheadline)
                            HStack {
                                Label(privateConfig.priceDisplay.usd, systemImage: "dollarsign.circle")
                                Spacer()
                                Text(privateConfig.priceDisplay.local)
                                    .foregroundStyle(.secondary)
                            }
                            Text("Moeda aproximada: \(privateConfig.priceDisplay.localCurrency) - \(privateConfig.priceDisplay.teamName)")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            Text("Limite tecnico inicial: \(privateConfig.participantLimit) participantes.")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }

                        Link(destination: privateGroupURL) {
                            Label("Saiba mais", systemImage: "info.circle")
                        }
                    } else {
                        Text("Informacoes de grupo privado indisponiveis no momento.")
                            .foregroundStyle(.secondary)
                    }
                } footer: {
                    Text("O preco final sera exibido pela Apple ou Google Play no momento da compra.")
                }

                Section("E-mail") {
                    Button {
                        Task { await resendConfirmation() }
                    } label: {
                        Label("Reenviar confirmacao de e-mail", systemImage: "envelope")
                    }
                } footer: {
                    Text("Verifique tambem a caixa de spam.")
                }

                if let localMessage {
                    Section {
                        Text(localMessage)
                            .font(.footnote)
                            .foregroundStyle(.secondary)
                    }
                }

                Section {
                    Button(role: .destructive) {
                        showingDeleteSheet = true
                    } label: {
                        Label("Excluir minha conta", systemImage: "trash")
                    }

                    Button {
                        Task { await appState.logout() }
                    } label: {
                        Label("Sair", systemImage: "rectangle.portrait.and.arrow.right")
                    }
                }
            }
            .navigationTitle("Conta")
            .task {
                await loadPrivateConfig()
            }
            .refreshable {
                await loadPrivateConfig()
            }
            .sheet(isPresented: $showingDeleteSheet) {
                DeleteAccountView()
                    .environmentObject(appState)
            }
        }
    }

    private func loadPrivateConfig() async {
        isLoadingConfig = true
        do {
            privateConfig = try await appState.api.privateGroupConfig()
        } catch {
            localMessage = error.localizedDescription
        }
        isLoadingConfig = false
    }

    private func resendConfirmation() async {
        localMessage = nil
        do {
            try await appState.api.reenviarConfirmacaoEmail()
            localMessage = "E-mail de confirmacao enviado. Verifique spam."
        } catch {
            localMessage = error.localizedDescription
        }
    }
}

private struct DeleteAccountView: View {
    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss
    @State private var senha = ""
    @State private var confirmacao = ""

    private var canDelete: Bool {
        !senha.isEmpty && confirmacao.trimmingCharacters(in: .whitespacesAndNewlines).uppercased() == "EXCLUIR"
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Text("Esta acao remove seus dados pessoais, palpites, pontuacoes e historico vinculados a conta. Ela nao pode ser desfeita.")
                        .foregroundStyle(.secondary)
                }

                Section("Confirmacao") {
                    SecureField("Confirme sua senha", text: $senha)
                        .textContentType(.password)
                    TextField("Digite EXCLUIR", text: $confirmacao)
                        .textInputAutocapitalization(.characters)
                }

                if let message = appState.message {
                    Section {
                        Text(message)
                            .foregroundStyle(.red)
                    }
                }

                Section {
                    Button(role: .destructive) {
                        Task {
                            await appState.deleteAccount(senha: senha, confirmacao: confirmacao)
                            if !appState.isAuthenticated {
                                dismiss()
                            }
                        }
                    } label: {
                        Label(appState.isLoading ? "Excluindo..." : "Excluir definitivamente", systemImage: "trash")
                            .frame(maxWidth: .infinity)
                    }
                    .disabled(!canDelete || appState.isLoading)
                }
            }
            .navigationTitle("Excluir conta")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancelar") {
                        dismiss()
                    }
                }
            }
        }
    }
}
