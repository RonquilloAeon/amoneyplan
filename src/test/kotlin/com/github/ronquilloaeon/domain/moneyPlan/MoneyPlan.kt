package com.github.ronquilloaeon.domain.moneyPlan

import org.junit.Test
import java.math.BigDecimal
import kotlin.test.assertEquals
import kotlin.test.assertFalse

class MoneyPlanTest {
    @Test fun accountBalanceInfo() {
        val bucket1 = Bucket.create(null, "Balance", BucketType.BALANCE, Money(BigDecimal("1000")))
        val bucket2 = Bucket.create(null, "Rent", BucketType.HOUSING, Money(BigDecimal("-500")))

        val account1 = Account.create(null, "Checking A", listOf(bucket1, bucket2))
        val moneyPlan = MoneyPlan.create(null, listOf(account1))

        assertEquals(BigDecimal("500"), moneyPlan.balance)
        assertFalse(moneyPlan.isZero)
    }
}