import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var appState: AppState
    @State private var email = ""
    @State private var senha = ""

    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                Spacer()

                Image(systemName: "trophy.fill")
                    .font(.system(size: 54))
                    .foregroundStyle(.green)

                VStack(spacing: 6) {
                    Text("Bolao 3")
                        .font(.largeTitle.bold())
                    Text("Competicao de Futebol 2026")
                        .foregroundStyle(.secondary)
                }

                VStack(spacing: 12) {
                    TextField("E-mail", text: $email)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.emailAddress)
                        .textContentType(.username)
                        .padding()
                        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 10))

                    SecureField("Senha", text: $senha)
                        .textContentType(.password)
                        .padding()
                        .background(.thinMaterial, in: RoundedRectangle(cornerRadius: 10))
                }

                if let message = appState.message {
                    Text(message)
                        .font(.footnote)
                        .foregroundStyle(.red)
                        .multilineTextAlignment(.center)
                }

                Button {
                    Task {
                        await appState.login(email: email, senha: senha)
                    }
                } label: {
                    Label(appState.isLoading ? "Entrando..." : "Entrar", systemImage: "rectangle.portrait.and.arrow.right")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .disabled(appState.isLoading || email.isEmpty || senha.isEmpty)

                NavigationLink {
                    RegisterView()
                } label: {
                    Label("Criar conta", systemImage: "person.crop.circle.badge.plus")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.bordered)

                Spacer()
            }
            .padding(24)
        }
    }
}
