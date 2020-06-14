package com.github.ronquilloaeon.domain

import org.apache.commons.lang3.builder.EqualsBuilder
import org.apache.commons.lang3.builder.HashCodeBuilder

abstract class Entity<T : Any>(val id: T) {
    private val events: MutableList<Event> = mutableListOf()

    override fun equals(other: Any?): Boolean {
        if (other!!.javaClass != this.javaClass) {
            return false
        }
        return EqualsBuilder()
                .append(this.id, (other as Entity<*>).id) // Only on the ID!
                .isEquals
    }

    override fun hashCode(): Int {
        return HashCodeBuilder()
                .append(id) // Only on the ID!
                .toHashCode()
    }
}