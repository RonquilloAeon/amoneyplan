package com.github.ronquilloaeon

import com.github.ronquilloaeon.domain.moneyPlan.Account
import com.github.ronquilloaeon.domain.moneyPlan.Bucket
import com.github.ronquilloaeon.domain.moneyPlan.BucketType
import com.github.ronquilloaeon.domain.moneyPlan.Money
import com.github.ronquilloaeon.domain.moneyPlan.MoneyPlan
import java.math.BigDecimal

fun createMoneyPlanUseCase() {
    val mp = MoneyPlan.create()
    println("${mp.id}")

    val bucket = Bucket.create(null, "Balance", BucketType.BALANCE, Money(BigDecimal("2500")))
    println("${bucket.id}, ${bucket.name}, ${bucket.type.short_desc}, ${bucket.amount}")

    val checkingAccount = Account.create(null, "Checking A", listOf(bucket))

    println("${checkingAccount.id}, ${checkingAccount.name}, ${checkingAccount.buckets.joinToString { it.name }}")
}

fun main(args: Array<String>) {
    createMoneyPlanUseCase()
}
