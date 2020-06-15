package com.github.ronquilloaeon.domain.moneyPlan

import com.github.ronquilloaeon.domain.Entity
import java.math.BigDecimal
import java.util.UUID

class MoneyPlan(id: UUID, val accounts: List<Account> = listOf()) : Entity<UUID>(id) {
    val balance: BigDecimal
        get() {
            val balances = accounts.map { it.balance }
            return balances.fold(BigDecimal.ZERO, BigDecimal::add)
        }
    val isZero: Boolean
        get() {
            return balance.compareTo(BigDecimal.ZERO) == 0
        }

    fun addAccount(account: Account) {

    }

    fun removeAccount(accountId: UUID) {

    }

    companion object {
        fun create(id: UUID? = null, accounts: List<Account> = listOf()) : MoneyPlan {
            val entityId = id ?: UUID.randomUUID()

            return MoneyPlan(entityId, accounts)
        }
    }
}