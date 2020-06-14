package com.github.ronquilloaeon

import com.github.ronquilloaeon.domain.moneyPlan.MoneyPlan

fun createMoneyPlanUseCase() {
    val mp = MoneyPlan.create()
    println("${mp.id}")
}

fun main(args: Array<String>) {
    createMoneyPlanUseCase()
}
