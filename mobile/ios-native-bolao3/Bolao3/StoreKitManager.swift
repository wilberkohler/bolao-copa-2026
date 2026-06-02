import Foundation
import StoreKit

struct PrivateGroupPurchase {
    let productId: String
    let transactionId: String
    let originalTransactionId: String?
}

enum PrivateGroupPurchaseError: LocalizedError {
    case productUnavailable
    case pending
    case userCancelled
    case failedVerification

    var errorDescription: String? {
        switch self {
        case .productUnavailable:
            return "Compra indisponivel no momento."
        case .pending:
            return "A compra ainda esta pendente de aprovacao."
        case .userCancelled:
            return "Compra cancelada."
        case .failedVerification:
            return "Nao foi possivel verificar a compra."
        }
    }
}

@MainActor
final class StoreKitManager: ObservableObject {
    @Published var product: Product?
    @Published var isLoadingProduct = false
    @Published var isPurchasing = false
    @Published var errorMessage: String?

    private let productId: String

    init(productId: String = "private_group_2026") {
        self.productId = productId
    }

    var displayPrice: String? {
        product?.displayPrice
    }

    func loadProduct(productId: String? = nil) async {
        isLoadingProduct = true
        errorMessage = nil
        do {
            let products = try await Product.products(for: [productId ?? self.productId])
            product = products.first
            if product == nil {
                errorMessage = PrivateGroupPurchaseError.productUnavailable.localizedDescription
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoadingProduct = false
    }

    func purchase() async throws -> PrivateGroupPurchase {
        guard let product else {
            throw PrivateGroupPurchaseError.productUnavailable
        }

        isPurchasing = true
        defer { isPurchasing = false }

        let result = try await product.purchase()
        switch result {
        case .success(let verification):
            let transaction = try checkVerified(verification)
            let purchase = makePurchase(from: transaction)
            await transaction.finish()
            return purchase
        case .pending:
            throw PrivateGroupPurchaseError.pending
        case .userCancelled:
            throw PrivateGroupPurchaseError.userCancelled
        @unknown default:
            throw PrivateGroupPurchaseError.productUnavailable
        }
    }

    func restorePrivateGroupPurchase() async throws -> PrivateGroupPurchase? {
        try await AppStore.sync()
        for await entitlement in Transaction.currentEntitlements {
            let transaction = try checkVerified(entitlement)
            if transaction.productID == productId {
                return makePurchase(from: transaction)
            }
        }
        return nil
    }

    private func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .verified(let safe):
            return safe
        case .unverified:
            throw PrivateGroupPurchaseError.failedVerification
        }
    }

    private func makePurchase(from transaction: Transaction) -> PrivateGroupPurchase {
        PrivateGroupPurchase(
            productId: transaction.productID,
            transactionId: String(transaction.id),
            originalTransactionId: String(transaction.originalID)
        )
    }
}
