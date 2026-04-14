**`funboost` vs `celery` Performance Benchmark Conclusions**

### 2.6.1 `funboost` vs `celery` Controlled Variable Methodology

Using the classic controlled variable method for testing.

Common conditions:

Tested on win11 + python3.9 + local Redis middleware + AMD R7 5800H CPU + single-thread concurrency mode + identical consumer function logic.

Difference:

`funboost` vs `celery 5.xx`


### 2.6.2 `funboost` vs `celery` Publishing Performance Comparison

`funboost`: Published 100,000 messages in 5 seconds, publishing 1,000 messages every 0.05 seconds, averaging 20,000 messages per second.

`celery`: Published 100,000 messages in 110 seconds, publishing 1,000 messages every 1.1 seconds, averaging 900 messages per second.

Result: `funboost` publishing performance is approximately **22x** that of `celery`.

### 2.6.3 `funboost` vs `celery` Consumption Performance Comparison

`funboost`: Consumed 1,000 messages every 0.07 seconds on average, approximately 14,000 messages per second.

`celery`: Consumed 1,000 messages every 3.6 seconds on average, approximately 300 messages per second.

Result: `funboost` consumption performance is approximately **46x** that of `celery`.

### 2.6.4 `funboost` vs `celery` Overall Performance Comparison

Under identical hardware and test conditions (win11 + python3.9 + local Redis middleware + AMD R7 5800H CPU + single-thread concurrency mode + same consumer function), \
`funboost` significantly outperforms `celery` in both message publishing and consumption. `funboost` publishing performance is `22`x that of `celery`, and `funboost` consumption performance is `46`x that of `celery`. \
Therefore, `funboost` does not merely beat `celery` by some percentage — it outperforms by a full order of magnitude. `funboost`'s performance lead is absolute and unquestionable.


### 2.6.5 Latest Performance Comparison — January 2026

Running the function `def fun(x): pass`,
funboost consumption performance is 100x that of celery,
and publishing performance is 50x that of celery.
