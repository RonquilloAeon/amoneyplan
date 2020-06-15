package com.github.ronquilloaeon.domain.moneyPlan

import com.github.ronquilloaeon.domain.Entity
import java.util.UUID

class Account(id: UUID, val name: String, var buckets: List<Bucket>) : Entity<UUID>(id) {
    fun addBucket() {

    }

    fun removeBucket() {

    }

    companion object {
        fun create(id: UUID? = null, name: String, buckets: List<Bucket>) : Account {
            val entityId = id ?: UUID.randomUUID()

            return Account(entityId, name, buckets)
        }
    }
}