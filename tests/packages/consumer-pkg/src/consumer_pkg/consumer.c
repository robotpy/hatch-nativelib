#include "consumer.h"
#include "provider.h"

int consumer_twice_plus_one(int value) {
    return provider_add(value, value) + 1;
}
