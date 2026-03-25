from llist import sllist

# Create an empty linked list
ll = sllist()

# Append a node to the tail of the linked list
ll.append(1)

# Prepend a node to the head of the linked list
ll.appendleft(2)

# Remove a specific node
ll.remove(1)

# Get the length of the linked list
length = len(ll)

# Iterate through the linked list
for node in ll:
    print(node.value)
