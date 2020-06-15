# A Money Plan
This spin on budgeting is essentially zero-based budgeting. I use it to disperse funds. The way
I've been able to get myself to manage my finances is by only budgeting. I do not track every expense (I know,
I'm a heretic). Of course, for my budgeting to work, I have a good idea of how much I spend and what my fixed expenses
are. However, I don't obsess with tracking every expense. I've been using this method for over a year (since early
2019), and it helped me pay off nearly $18k in debt. Now it's helping me save for retirement.

By using many accounts, I've created a digital version of the envelope system. I used the cash envelope system for a
while, but it's annoying because you have to go to an ATM to get cash then you have to remember to carry all your
envelopes wherever you go. And I don't like paying in cash, it's tedious.

This plan assumes that you have a checking account where you receive direct deposits. From this account, you disperse
funds to other accounts, to savings/investments, and expenses.

Do not use this checking account to pay for day-to-day stuff (groceries, gas, clothes, etc). Open a separate checking
account with a debit card that you'll use to pay for groceries, eating out, clothing, hair cuts, etc. I personally
opened an account in a separate bank.

I do not recommend this method if you are unable to control your spending. If you struggle with willpower, a cash
envelope system may be better for you, at least to begin with.

## Sample Money Plan
Each money plan correlates to a paycheck. The day I get paid, I create a money plan to immediately move money to all
buckets (gotta put money to work). I get paid twice a month, so I create two money plans each month.

Notice that Checking B has two savings buckets in addition to a cash bucket. This is because I transfer the money for
all those three buckets from Checking A to Checking B. When the funds are deposited in Checking B, I go into that bank's
app and I transfer the funds for the two savings buckets to their respective accounts.

This is a method that works for me, you can use the account/bucket system as you see fit. I do it this way because I
use my Checking A account to disperse funds and ensure that I'm utilizing my money in a way that achieves my goals.

Note that you don't want your checking account to ever hit actual zero or go negative because you may be hit with fees.
Thus, every bucket has a buffer built into it. Thus, the balance fluctuates from pay period to pay period, even though
my income is steady. Whatever extra balance I have, I put towards savings/investments or paying off a splurge.

| Debit/Credit | Account           | Bucket                          | Amount |
|--------------|-------------------|---------------------------------|--------|
| Credit       | Checking A        | Balance                         | 2500   |
|              |                   |                                 | = 2500 |
| Debit        | Checking A        | Rent                            | (700)  |
|              |                   | Cell Bill                       | (150)  |
|              |                   |                                 | = 1650 |
| Debit        | Investment Bank A | General Investing               | (250)  |
|              |                   |                                 | = 1400 |
| Debit        | Investment Bank B | IRA                             | (200)  |
|              |                   |                                 | = 1200 |
| Debit        | Checking B        | Cash (Groceries, Clothing, Fun) | (600)  |
|              |                   | Emergency Fund                  | (100)  |
|              |                   | Car Repairs Savings             | (100)  |
|              |                   |                                 | = 400  |
| Debit        | Credit Card A     | Gas                             | (100)  |
|              |                   | Splurge                         | (200)  |
|              |                   | Subscriptions                   | (50)   |
|              |                   |                                 | = 50   |
| Debit        | Credit Card B     | Debt                            | (50)   |
|              |                   |                                 | = 0    |

## Misc Technical Stuff

### Resources
- https://www.baeldung.com/maven-multi-module-project-java-jpms
- https://mkyong.com/maven/maven-how-to-create-a-multi-module-project/
- https://dzone.com/articles/maven-multi-module-project-with-versioning
- https://github.com/jitpack/maven-modular
- https://stackoverflow.com/a/808534/5340241
- https://stackoverflow.com/questions/29712865/maven-cannot-resolve-dependency-for-module-in-same-multi-module-project
- https://github.com/bringmeister/ddd-with-kotlin
- https://khalilstemmler.com/articles/typescript-domain-driven-design/aggregate-design-persistence/

### Commands
`mvn archetype:generate -DarchetypeGroupId=org.jetbrains.kotlin -DarchetypeArtifactId=kotlin-archetype-jvm -Dgroupid=com.github.ronquilloaeon -DartifactId=domain`
