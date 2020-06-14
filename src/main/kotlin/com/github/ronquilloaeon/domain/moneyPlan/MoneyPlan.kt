package com.github.ronquilloaeon.domain.moneyPlan

import com.github.ronquilloaeon.domain.Entity
import java.util.UUID

class MoneyPlan(id: UUID) : Entity<UUID>(id) {
    companion object {
        fun create(id: UUID? = null) : MoneyPlan {
            val entityId = id ?: UUID.randomUUID()

            return MoneyPlan(entityId)
        }
    }
}