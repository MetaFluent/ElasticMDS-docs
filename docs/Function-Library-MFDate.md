# Business Day Functions (MFDate)

The `MFDate` library works with dates: today's date in a time zone, a date some days later, the days between two dates, and the same over business days read from a calendar. Business days come from the calendars the [calendar adapter](Configuration-Calendar.md) publishes, so a settlement date can follow a market's holidays and change when a holiday is added.

**Audience:** Developer.

---

## Calling the functions

Call a function by library and function name, as any [function library](Function-Libraries.md) is called. A date argument is a DATE column or text written `yyyy-MM-dd`, and a date's text form is `yyyy-MM-dd`.

| Function | Result | Meaning |
|---|---|---|
| `MFDate.TODAY()` / `MFDate.TODAY('<zone>')` | DATE | Today's date in the zone, an IANA zone name such as `America/New_York`. With no argument, in the server's system time zone. It changes at that zone's midnight, and rows that use it recompute then. |
| `MFDate.ADD_DAYS(date, days)` | DATE | The date that many days later; earlier for a negative count. |
| `MFDate.DAYS_BETWEEN(start, end)` | DECIMAL, a whole number | The days from `start` to `end`; negative when `end` is earlier. |
| `MFDate.IS_BUSINESS_DAY(date, calendar, 'Calendars.<set>')` | BOOLEAN | Whether the date is a business day in the calendar. |
| `MFDate.ADD_BUSINESS_DAYS(date, n, calendar, 'Calendars.<set>')` | DATE | The date `n` business days after `date`; before it for a negative `n`. With `n` = 0 the result is `date` itself when it is a business day, otherwise the next business day. |
| `MFDate.BUSINESS_DAYS_BETWEEN(start, end, calendar, 'Calendars.<set>')` | DECIMAL, a whole number | The business days after `start` up to and including `end`; negative when `end` is the earlier. |
| `MFDate.CALENDAR(calendar, 'Calendars.<set>')` | STRING | The calendar name as the functions read it: its parts trimmed, sorted and joined by `+`. `'TARGET2 + SIFMA_US'` gives `SIFMA_US+TARGET2`. |

`NOT MFDate.IS_BUSINESS_DAY(...)` is supported in a `WHERE` clause.

---

## Calendars

The last argument of the business day functions names the calendar set as a text constant, `'Calendars.<set>'`. For the set `Site` it is `'Calendars.Site'`. The calendar adapter publishes the set; see [Business Calendars](Configuration-Calendar.md).

The calendar argument is any expression: a constant such as `'SIFMA_US'`, or a column such as `b.SETTLE_CAL`. One statement can use different calendars, per row or per column.

To use several calendars at once, join them with `+`: `'SIFMA_US+TARGET2'`. Spaces and order do not matter. A day is then a business day only when it is one in every calendar named, over the dates all of them cover.

---

## Following the calendar

The functions follow the calendar. When a holiday is added to or removed from a calendar's files, the rows that use the calendar recompute in an open statement. No restart or new query is needed. A calendar that is added to a set after a statement started is used by statements started from then on.

---

## Results that are NULL

A function returns NULL when:

- an argument is NULL or cannot be used;
- the set does not have the calendar;
- the date is outside the calendar's `first_date` to `last_date`, or the result would fall outside it;
- several calendars have no date in common.

A date or a count that is NULL has no value. `IS_BUSINESS_DAY` gives false in each of these cases.

---

## Example

This example works as written against the sample set once the calendar adapter is enabled. Each bond settles on a business day in its own calendar, counted from today's date in New York.

```sql
SELECT ISIN,
       MFDate.ADD_BUSINESS_DAYS(MFDate.TODAY('America/New_York'), SETTLE_DAYS, SETTLE_CAL, 'Calendars.Site') AS SETTLE_DATE,
       MFDate.IS_BUSINESS_DAY(MATURITY, SETTLE_CAL, 'Calendars.Site') AS MATURES_ON_BUSINESS_DAY
FROM BOND_REF
```

A bond whose `SETTLE_CAL` is `SIFMA_US+TARGET2` settles on a day that is a business day in both calendars.

---

## Where to go next

- [Business Calendars](Configuration-Calendar.md) - the calendars, sets and tables the functions read.
- [Function Libraries](Function-Libraries.md) - calling functions and listing a library's functions.
- [JDBC Application Development](Develop-JDBC.md) - the SQL you can use with them.
