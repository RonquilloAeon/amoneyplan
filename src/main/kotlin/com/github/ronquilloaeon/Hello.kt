package com.github.ronquilloaeon

import com.github.ronquilloaeon.domain.moneyPlan.Account
import com.github.ronquilloaeon.domain.moneyPlan.Bucket
import com.github.ronquilloaeon.domain.moneyPlan.BucketType
import com.github.ronquilloaeon.domain.moneyPlan.Money
import com.github.ronquilloaeon.domain.moneyPlan.MoneyPlan
import java.math.BigDecimal
import java.util.Date

fun createMoneyPlanUseCase() {
    val mp = MoneyPlan.create()
    println("${mp.id}")

    val bucket1 = Bucket.create(null, "Balance", BucketType.BALANCE, Money(BigDecimal("4500")))
    println("${bucket1.id}, ${bucket1.name}, ${bucket1.type.short_desc}, ${bucket1.balance}")
    val bucket2 = Bucket.create(null, "Rent", BucketType.HOUSING, Money(BigDecimal("-700")))
    println("${bucket2.id}, ${bucket2.name}, ${bucket2.type.short_desc}, ${bucket2.balance}")

    val checkingAccount = Account.create(null, "Checking A", listOf(bucket1, bucket2))
    println("checking balance ${checkingAccount.balance}")
    println()

    val bucket3 = Bucket.create(null, "Cash", BucketType.PERSONAL, Money(BigDecimal("-600")))
    println("${bucket3.id}, ${bucket3.name}, ${bucket3.type.short_desc}, ${bucket3.balance}")
    val bucket4 = Bucket.create(null, "Emergency Fund", BucketType.EMERGENCY_FUND, Money(BigDecimal("-3200")))
    println("${bucket4.id}, ${bucket4.name}, ${bucket4.type.short_desc}, ${bucket4.balance}")

    val checkingBAccount = Account.create(null, "Checking B", listOf(bucket3, bucket4))
    println("checking b balance ${checkingBAccount.balance}")
    println()

    val moneyPlan = MoneyPlan.create(null, listOf(checkingAccount, checkingBAccount))
    println("mp balance > ${moneyPlan.balance} | is zero > ${moneyPlan.isZero}")
    println()

    println("${checkingAccount.id}, ${checkingAccount.name}, ${checkingAccount.buckets.joinToString { it.name }}")
    println(Date())
}

fun main(args: Array<String>) {
    createMoneyPlanUseCase()
}