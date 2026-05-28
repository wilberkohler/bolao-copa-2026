import SwiftUI

struct RegisterView: View {
    @EnvironmentObject private var appState: AppState
    @Environment(\.dismiss) private var dismiss
    @State private var nome = ""
    @State private var email = ""
    @State private var apelido = ""
    @State private var senha = ""
    @State private var codigoGrupo = ""
    @State private var grupos: [GrupoCadastro] = []
    @State private var selectedGrupoId: Int?
    @State private var localMessage: String?
    @State private var isLoadingGroups = false

    private var selectedGrupo: GrupoCadastro? {
        grupos.first { $0.id == selectedGrupoId }
    }

    private var canSubmit: Bool {
        !nome.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty &&
        !email.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty &&
        !apelido.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty &&
        !senha.isEmpty &&
        !(selectedGrupo?.requerCodigo == true && codigoGrupo.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
    }

    var body: some View {
        Form {
            Section("Dados da conta") {
                TextField("Nome", text: $nome)
                    .textContentType(.name)
                TextField("E-mail", text: $email)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.emailAddress)
                    .textContentType(.emailAddress)
                TextField("Apelido", text: $apelido)
                SecureField("Senha", text: $senha)
                    .textContentType(.newPassword)
            }

            Section {
                if isLoadingGroups {
                    ProgressView("Carregando grupos...")
                } else {
                    Picker("Grupo", selection: $selectedGrupoId) {
                        Text("Sem grupo").tag(Int?.none)
                        ForEach(grupos) { grupo in
                            Text(grupo.requerCodigo ? "\(grupo.nome) (privado)" : grupo.nome)
                                .tag(Optional(grupo.id))
                        }
                    }
                }

                if selectedGrupo?.requerCodigo == true {
                    TextField("Codigo do grupo", text: $codigoGrupo)
                        .textInputAutocapitalization(.characters)
                }
            } header: {
                Text("Grupo")
            } footer: {
                Text("Grupos abertos podem ser escolhidos livremente. O grupo WK3 exige codigo.")
            }

            if let localMessage {
                Section {
                    Text(localMessage)
                        .foregroundStyle(.red)
                }
            }

            Section {
                Button {
                    Task {
                        await submit()
                    }
                } label: {
                    Label(appState.isLoading ? "Cadastrando..." : "Criar conta", systemImage: "person.crop.circle.badge.plus")
                        .frame(maxWidth: .infinity)
                }
                .disabled(appState.isLoading || !canSubmit)
            }
        }
        .navigationTitle("Cadastro")
        .task {
            await loadGroups()
        }
    }

    private func loadGroups() async {
        isLoadingGroups = true
        localMessage = nil
        do {
            grupos = try await appState.api.gruposCadastro()
        } catch {
            localMessage = error.localizedDescription
        }
        isLoadingGroups = false
    }

    private func submit() async {
        localMessage = nil
        await appState.registrar(
            nome: nome,
            email: email,
            apelido: apelido,
            senha: senha,
            grupoId: selectedGrupoId,
            codigoGrupo: selectedGrupo?.requerCodigo == true ? codigoGrupo : nil
        )
        if appState.user != nil {
            dismiss()
        } else {
            localMessage = appState.message
        }
    }
}
