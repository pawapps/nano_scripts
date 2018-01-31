# raiiblocks_bouncer

This scripts uses two RaiBlocks accounts on the same wallet and bounces a given value between them as fast as possible.  It is single threaded and all work is calculated in series as well.

## Usage

In order to run the script a bit of legwork needs to be done on setup.

* Account 2 must have the given balance in main.  It will be the first to send (to Account 1)

* Enter account number into account_1 (in main)

* Enter account number into account_2 (in main)

* Enter wallet ID into wallet (in main)

* Enter wallet password into password (in global)

## Experiments

I have used this scripts to conduct a few experiments with a node hosted on various Amazon AWS EC2 instances.  Below are links to the write-ups:

* https://www.reddit.com/r/RaiBlocks/comments/7r7ixr/i_processed_332_transactions_in_24_hours_on_aws/

* https://www.reddit.com/r/RaiBlocks/comments/7rto9o/i_sent_and_then_received_1463_transactions_in_30/
