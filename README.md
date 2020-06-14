# A Money Plan
This spin on budgeting is essentially zero-based budgeting except that I use it primarily to disperse funds. The way
I've been able to get myself to manage my finances is by only budgeting. I do not track every expense (I know,
I'm a heretic). Of course, for my budgeting to work, I have a good idea of how much I spend and what my fixed expenses
are.

By using many accounts, I've created a digital version of the envelope system. I used the cash envelope system for a
while, but it's annoying because you have to go to an ATM to get cash then you have to remember to carry all your
envelopes wherever you go. And I don't like paying in cash, it's tedious.

This plan assumes that you have a checking account where you receive direct deposits. From this account, you disperse
funds to other accounts, to savings/investments, and expenses.

Do not use this checking account to pay for day-to-day stuff (groceries, gas, clothes, etc). Open a separate checking
account with a debit card that you'll use to pay for groceries, eating out, clothing, hair cuts, etc. I personally
opened an account in a separate bank.

## Sample Money Plan
Each money plan correlates to a paycheck. The day I get paid, I create a money plan to immediately move money to all
buckets (gotta put money to work). I get paid twice a month, so I create two money plans each month.

| Debit/Credit | Account           | Bucket              | Amount |
|--------------|-------------------|---------------------|--------|
| Credit       | Bank A            | Checking            | 2500   |
|              |                   |                     |        |
| Debit        | Bank A            | Rent                | (700)  |
|              |                   | Cell Bill           | (150)  |
|              |                   |                     |        |
| Debit        | Investment Bank A | General Investing   | (250)  |
|              |                   |                     |        |
| Debit        | Investment Bank B | IRA                 | (200)  |
|              |                   |                     |        |
| Debit        | Bank B            | Checking            | (600)  |
|              |                   | Emergency Fund      | (100)  |
|              |                   | Car Repairs Savings | (100)  |
|              |                   |                     |        |
| Debit        | Credit Card A     | Gas                 | (100)  |
|              |                   | Splurge             | (200)  |
|              |                   | Subscriptions       | (100)  |
|              |                   |                     |        |
|              |                   |                     | 0      |

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
