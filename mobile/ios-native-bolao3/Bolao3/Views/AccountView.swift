import SwiftUI
import UIKit

struct AccountView: View {
    @EnvironmentObject private var appState: AppState
    @StateObject private var storeKit = StoreKitManager()
    @State private var privateConfig: PrivateGroupConfigResponse?
    @State private var isLoadingConfig = false
    @State private var localMessage: String?
    @State private var activatedGroup: PrivateGroupActivation?
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

                Section {
                    ShareLink(item: inviteText) {
                        Label("Convidar amigo", systemImage: "square.and.arrow.up")
                    }

                    Button {
                        UIPasteboard.general.string = inviteText
                        localMessage = "Convite copiado."
                    } label: {
                        Label("Copiar convite", systemImage: "link")
                    }
                } header: {
                    Text("Convite")
                } footer: {
                    Text(inviteURL.absoluteString)
                }

                Section {
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
                            if let storePrice = storeKit.displayPrice {
                                Text("Preco na App Store: \(storePrice)")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }

                        if storeKit.isLoadingProduct {
                            ProgressView("Consultando App Store...")
                        }

                        if let storeError = storeKit.errorMessage {
                            Text(storeError)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }

                        Button {
                            Task { await buyPrivateGroup() }
                        } label: {
                            Label(storeKit.isPurchasing ? "Processando compra..." : "Comprar grupo privado", systemImage: "cart")
                        }
                        .disabled(storeKit.product == nil || storeKit.isPurchasing)

                        Button {
                            Task { await restorePrivateGroupPurchase() }
                        } label: {
                            Label("Restaurar compra", systemImage: "arrow.clockwise")
                        }

                        Link(destination: privateGroupURL) {
                            Label("Saiba mais", systemImage: "info.circle")
                        }
                    } else {
                        Text("Informacoes de grupo privado indisponiveis no momento.")
                            .foregroundStyle(.secondary)
                    }
                } header: {
                    Text("Grupo privado")
                } footer: {
                    Text("O preco final sera exibido pela Apple ou Google Play no momento da compra.")
                }

                if let activatedGroup {
                    Section("Seu grupo privado") {
                        VStack(alignment: .leading, spacing: 8) {
                            Text(activatedGroup.nome)
                                .font(.headline)
                            Text("Participantes: \(activatedGroup.participantes)/\(activatedGroup.limiteParticipantes)")
                                .foregroundStyle(.secondary)
                            Text(activatedGroup.conviteURL)
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            if let codigo = activatedGroup.codigoAcesso {
                                Text("Codigo de acesso: \(codigo)")
                                    .font(.headline)
                            }
                        }

                        Button {
                            UIPasteboard.general.string = groupInviteText(activatedGroup)
                            localMessage = "Convite do grupo copiado."
                        } label: {
                            Label("Copiar convite do grupo", systemImage: "link")
                        }
                    } footer: {
                        Text("Guarde o codigo de acesso: novos participantes precisam dele para entrar no grupo.")
                    }
                }

                Section {
                    Button {
                        Task { await resendConfirmation() }
                    } label: {
                        Label("Reenviar confirmacao de e-mail", systemImage: "envelope")
                    }
                } header: {
                    Text("E-mail")
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
                await storeKit.loadProduct(productId: privateConfig?.productId)
            }
            .refreshable {
                await loadPrivateConfig()
                await storeKit.loadProduct(productId: privateConfig?.productId)
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

    private func buyPrivateGroup() async {
        localMessage = nil
        do {
            let purchase = try await storeKit.purchase()
            try await activatePrivateGroup(with: purchase)
        } catch PrivateGroupPurchaseError.userCancelled {
            localMessage = "Compra cancelada."
        } catch {
            localMessage = error.localizedDescription
        }
    }

    private func restorePrivateGroupPurchase() async {
        localMessage = nil
        do {
            guard let purchase = try await storeKit.restorePrivateGroupPurchase() else {
                localMessage = "Nenhuma compra encontrada para restaurar."
                return
            }
            try await activatePrivateGroup(with: purchase)
        } catch {
            localMessage = error.localizedDescription
        }
    }

    private func activatePrivateGroup(with purchase: PrivateGroupPurchase) async throws {
        let response = try await appState.api.activatePrivateGroup(
            productId: purchase.productId,
            transactionId: purchase.transactionId,
            originalTransactionId: purchase.originalTransactionId
        )
        if let user = response.user {
            appState.user = user
            appState.clearCaches()
        }
        activatedGroup = response.grupo
        localMessage = response.message ?? "Grupo privado ativado."
    }

    private func groupInviteText(_ group: PrivateGroupActivation) -> String {
        var text = "Convide um amigo para participar:\n\(group.conviteURL)"
        if let codigo = group.codigoAcesso {
            text += "\nCodigo de acesso: \(codigo)"
        }
        return text
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
