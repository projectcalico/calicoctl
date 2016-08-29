# Tier Resource
Tiers are independent objects which are assigned
 contain an explicitly ordered set of policy objects.  Tiers are themselves ordered, and Calico applies policy in tier-order.  (Profiles are the lowest priority, coming after the lowest priority tier.)

### Sample YAML
The following YAML spec shows an example of all possible fields for a tier resource:
```
apiVersion: v1
kind: tier
metadata:
  name: tier1
spec:
  order: 100
```


#### Metadata
| name | description  | requirements                  | schema |
|------|--------------|-------------------------------|--------|
| name | The name of the tier. | | string |


#### TierSpec
| name     | description                                                          | requirements | schema |
|----------|----------------------------------------------------------------------|--------------|--------|
| order    | The order number, which indicates the order that this tier is used. Tiers with identical order numbers are ordered in lexicographical name order. The order number may be omitted indicating default (or highest) order - i.e. it is applied last. | | integer |
