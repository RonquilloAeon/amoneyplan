package com.github.ronquilloaeon.domain.moneyPlan

import com.github.ronquilloaeon.domain.Entity
import java.util.UUID

enum class BucketType(val short_desc: String, val operator: String) {
    BALANCE("balance", "+"),
    INCOME("income", "+"),

    DEBT("debt", "-"),
    EMERGENCY_EXPENSE("emergency_expense", "-"),
    EMERGENCY_FUND("emergency_fund", "-"),
    HEALTH("health", "-"),
    HOUSING("housing", "-"),
    INVESTMENT("investment", "-"),
    LOAN("loan", "-"),
    MISC_EXPENSE("miscellaneous_expense", "-"),
    PERSONAL("personal", "-"),
    SAVINGS("savings", "-"),
    TRANSPORTATION("transportation", "-"),
    WELLNESS("wellness", "-");

    init {
        val validOperators = arrayOf("+", "-")

        if (operator !in validOperators) {
            throw IllegalArgumentException("Operator not of type: ${validOperators.joinToString(" or ")}")
        }
    }

    companion object {
        private val map = BucketType.values().associateBy(BucketType::short_desc)
        operator fun get(short_desc: String) = map[short_desc]
    }
}

class Bucket(id: UUID, val name: String, val type: BucketType, val balance: Money) : Entity<UUID>(id) {
    companion object {
        fun create(id: UUID? = null, name: String, type: BucketType, balance: Money) : Bucket {
            val entityId = id ?: UUID.randomUUID()

            return Bucket(entityId, name, type, balance)
        }
    }
}