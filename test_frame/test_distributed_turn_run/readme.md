
## User Requirement:

Each machine takes turns executing one message. The next machine only starts executing the next message after the previous machine has finished running its message.

Simply using a Redis distributed lock can only guarantee that only one thread across multiple machines is running a given code block at any time, ensuring only one machine is processing a message. However, it cannot guarantee that each machine waits for the previous one to finish before starting — that is, a Redis lock alone does not guarantee that machines take turns executing messages in order.

```
The user has machine1, machine2, machine3, ..., machine10.
The user wants each machine to take turns fetching messages from queue1 and running them.
Meaning: machine1 fetches msg1, runs it to completion; then machine2 fetches msg2 and runs it to completion; then machine3 fetches msg3 and runs it to completion; and so on, cycling repeatedly.
```

The user's real-world use case is using a large number of physical machine IPs to circumvent anti-scraping measures.

```
This user does not use an IP proxy pool. Instead, they use the real IPs of multiple physical machines to bypass anti-scraping, wanting each machine to take turns requesting URLs.
At the same time, only one machine at a time runs the URL crawl in single-concurrency mode, to avoid triggering IP-based anti-scraping.
The user does not want to use SSH to connect to remote machines and run curl crawlers, nor to set up an IP proxy service on physical machines — they just want to deploy the same Python crawler code normally on multiple machines.
```

## This demo uses a single machine to simulate the following special user requirement


```
This simulation uses two scripts on a single machine to simulate "two machines taking turns running messages, with only one machine executing a message at any time and only one message being executed at a time, with no concurrent message execution allowed".

In practice, the current machine's IP is obtained dynamically and automatically — there is no need for two separate files like run_execute_msg_on_host101.py and run_execute_msg_on_host102.py.
```



## Challenges and How funboost Solves This Requirement Easily

```
Challenge:
To ensure only one physical machine is crawling a URL at a time, a Redis distributed lock can handle that.

Solution:
To ensure each machine takes turns crawling one URL, a distributed lock alone is not enough.
So the solution uses single-thread concurrency mode + dispatching to different per-IP queues + RPC blocking to wait for the crawler function to complete before dispatching the next message.
This ensures only one machine is running at a time, and each machine takes its turn.

In funboost specifically:
A dispatcher reads from a main queue and pushes to sub-queues named after each machine's IP.
Write a message dispatcher function that must use single-thread concurrency mode, and inside it use RPC to block and wait for the result of the message execution function.
Write the actual message execution function, which must have RPC mode enabled (is_using_rpc_mode=True).
```

## Why This Is Very Difficult to Implement with Scrapy or Scrapy-Like Frameworks

```
With Scrapy or frameworks that mimic its API, this is extremely difficult to implement
because you have no idea which part of the framework to modify, and this kind of unusual requirement is hard to search for.

funboost is a function scheduling framework and URL dispatching framework — it is free and flexible, so any unusual or unique idea from the user does not require modifying the funboost framework itself.
```


## Script Descriptions

```
run_distribute_msg.py fetches messages from queue1 and takes turns dispatching them to sub-queues named after each IP in queue2.
The distribute_msg function uses single-thread concurrency mode and RPC mode to block until the function finishes before dispatching the next message to the next machine's queue,
thus ensuring each machine takes turns running one message (each machine takes turns fetching one URL seed and crawling it).

run_execute_msg_on_host101.py and run_execute_msg_on_host102.py are provided for the convenience of simulating two machines on a single machine.
In practice, you do not need to write these two separate files.
```
