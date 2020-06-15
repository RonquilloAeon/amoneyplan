package com.github.ronquilloaeon.domain.moneyPlan

import java.math.BigDecimal

data class Money(val amount: BigDecimal, val currency: String = "usd")