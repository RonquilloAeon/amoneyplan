package com.github.ronquilloaeon.domain.moneyPlan

import com.github.ronquilloaeon.domain.Event
import java.util.UUID

data class BucketAdded(val id: UUID) : Event

data class BucketRemoved(val id: UUID) : Event