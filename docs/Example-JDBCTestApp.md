# Worked Example: JDBCTestApp

`JDBCTestApp`, in the SDK, is a complete command-line query tool: give it a host and a SQL statement and it connects, runs the statement, and keeps a live table on screen as the market moves. It is the standard JDBC pattern plus the handful of things a real tool needs - options, a result set that is refreshed on a timer, and column formatting driven by the result's metadata. For the smallest possible program, start with [A first query](Develop-JDBC.md#a-first-query).

This page walks through the class section by section. The code below is the actual example, with the less instructive lines elided as `// ...`; the complete file is in the SDK at `examples/src/com/metafluent/examples/jdbctestapp/JDBCTestApp.java`, and `bin/JDBCTestApp.jar` contains it prebuilt.

**Audience:** Java developers who have read [JDBC Application Development](Develop-JDBC.md).

---

## Running it

```
java -jar bin/JDBCTestApp.jar -host localhost -head 20 \
     "SELECT RIC,DSPLY_NAME,BID,BIDSIZE,ASK,ASKSIZE,TRDPRC_1 FROM Quotes.RDF WHERE RIC IN ('SAB.L','BG.L','REX.L','WG.L')"
```

The query is the last argument; put it in double quotes so the single quotes around values reach the server unchanged. Press `Ctrl+C` to stop.

---

## 1. Command-line options

`main()` first evaluates the command line. The options are declared in the nested `AppOptions` class:

| Option | Default | Meaning |
|---|---|---|
| `-host` | `localhost` | Session server host. |
| `-port` | `8900` | Session server port. |
| `-user` | empty | User name for the connection. |
| `-catalog` | `Default` | Catalog to query. |
| `-maxRows` | no limit | Maximum number of rows in the result set. |
| `-maxThreads` | driver default | Size of the driver's thread pool. |
| `-ri` | `1000` | Refresh interval, in milliseconds. |
| `-di` | `1000` | Display interval, in milliseconds. |
| `-head` | no limit | Show only the first N rows. |
| `-noData` | off | Show the row count and refresh time, not the data. |
| `-closeIfNoResult` | off | Exit when the statement produces no result set. |

The remaining arguments are the SQL, which is required.

```java
// Evaluate command line options
AppOptions options = new AppOptions();
try {
	options.evaluate(args);
} catch (Exception e) {
	System.err.println(e.getMessage());
	options.printUsage(System.err);
	System.exit(-1);
}
```

---

## 2. Connect

Connection settings are ordinary JDBC `Properties`. The URL names the session server; the application name, version, and user identify this application to the server. `com.metafluent.jdbc.thread-pool-size` is optional and is set only when `-maxThreads` is given. `setCatalog` selects the catalog the query runs against.

```java
Properties properties = new Properties();
String url = String.format("jdbc:metafluent://%s:%d",AppOptions.Host,AppOptions.Port);
properties.setProperty("com.metafluent.jdbc.application-name", JDBCTestApp.class.getName());
properties.setProperty("com.metafluent.jdbc.application-version", "1.0.0");
properties.setProperty("com.metafluent.jdbc.user", AppOptions.User);
if ( AppOptions.MaxThreads > 0 )
	properties.setProperty("com.metafluent.jdbc.thread-pool-size", String.valueOf(AppOptions.MaxThreads));
try {
	Connection conn = DriverManager.getConnection(url, properties);
	conn.setCatalog(AppOptions.Catalog);
```

---

## 3. Create the statement

The statement is created `TYPE_SCROLL_SENSITIVE`, which is what makes the result set live (see [Live results](Develop-JDBC.md#live-results)). `setMaxRows` limits the size of the result when `-maxRows` is given.

```java
// Obtain a statement
Statement stmt = conn.createStatement(ResultSet.TYPE_SCROLL_SENSITIVE, ResultSet.CONCUR_UPDATABLE);
if ( AppOptions.MaxRows >= 0 ) stmt.setMaxRows(AppOptions.MaxRows);
```

---

## 4. Execute

The SQL is assembled from the remaining arguments and run with `execute()` rather than `executeQuery()`. `execute()` returns whether the statement produced a result set, so the tool can run statements that do not - `CREATE VIEW`, for example. With `-closeIfNoResult` the tool then closes the connection and exits; otherwise it keeps the session open, which keeps a newly created view available while the tool runs.

```java
// Build a sql command from the command line args
StringBuffer sqlBuffer = new StringBuffer();
for ( String str:AppOptions.SQL ) 
	sqlBuffer.append(" ").append(str);
System.err.println("Query is: " + sqlBuffer.toString());
// Execute the sql and see if it made some results
boolean gotResult = stmt.execute(sqlBuffer.toString());
if ( !gotResult && AppOptions.CloseIfNoResult ) {
	// No results, presumably an INSERT but we're done regardless
	conn.close();
	return;
}
if ( !gotResult ) {
	// Nothing to do so we'll just keep this session alive
	synchronized (stmt) {
		stmt.wait();
	}
	return;
}
```

---

## 5. Refresh and display

For a statement with a result set, `absolute(0)` refreshes the rows to their current values and positions the cursor before the first row. The loop then repeats two activities on separate timers: it refreshes with `absolute(0)` every refresh interval (`-ri`), and it walks the rows and prints them every display interval (`-di`). Refreshing more often than displaying is useful when you want to measure the cost of keeping the result current without printing every change.

```java
ResultSet resultSet = stmt.getResultSet();
resultSet.absolute(0);
// ...
do {
	// Print headers/data on the display interval
	if ( millisecondsSinceDisplay >= AppOptions.DisplayIntervalMilliseconds ) {
		// ...
		int rowCount = 0;
		while ( resultSet.next() ) {
			rowCount++;
			// Update row values and print
			if ( !AppOptions.NoData && 
					(AppOptions.DisplayHead < 0 || rowCount <= AppOptions.DisplayHead))
				printRow(resultSet);
		}
		// ...
	}
	// Wait a while
	try { 
		Thread.sleep(sleepInterval); 
		millisecondsSinceDisplay += AppOptions.RefreshIntervalMilliseconds;
		sleepInterval = AppOptions.RefreshIntervalMilliseconds;
	} catch (InterruptedException e) {
		break;
	}
	// Go back to the beginning
	long nanoBefore = System.nanoTime();
	resultSet.absolute(0);
	long nanoAfter = System.nanoTime();
	totalRefreshNanos += nanoAfter - nanoBefore;
	numberOfRefreshes++;
} while (true);
```

The time spent in each `absolute(0)` is measured with `System.nanoTime()` and averaged over each display interval. With `-noData` the tool prints that average instead of the rows, which makes it a convenient way to see how quickly a given query refreshes:

```java
if ( avgMillisPerRefresh > 0  ) {
	System.err.println(String.format("Rows refreshed [rowCount=%d, refresh MILLIseconds=%d]", rowCount, avgMillisPerRefresh));
} else {
	System.err.println(String.format("Rows refreshed [rowCount=%d, refresh MICROseconds=%d]", rowCount, avgNanosPerRefresh/1000));
}
```

---

## 6. Headers and column widths

`ResultSetMetaData` supplies everything needed to lay the table out. `printHeader()` reads the column count and each column's label to build a header line; `printRow()` sizes each column from `getColumnDisplaySize()` and reads values with `getString(i)`. If a value is wider than its column, the column is widened and the row is laid out again, so the table settles on the right widths after a few refreshes.

```java
static public void printHeader(ResultSet result) throws SQLException {
	if ( Header == null ) {
		Header = new StringBuffer();
		Header.append("|");
		for ( int i = 1; i <= result.getMetaData().getColumnCount(); i++ ) {
			int width = DisplayWidths == null ? result.getMetaData().getColumnDisplaySize(i) : DisplayWidths[i];
			String label = result.getMetaData().getColumnLabel(i);
			if ( label.length() > width && DisplayWidths != null ) {
				DisplayWidths[i] = label.length();
			}
			Header.append(String.format("%"+width+"s |", label));
		}
	// ...
static public void printRow(ResultSet result) {
	StringBuffer buffer = new StringBuffer();
	try {
		// ...
		for ( int i = 1; i <= result.getMetaData().getColumnCount(); i++ ) {
			int width = DisplayWidths[i];
			try {
				String value = result.getString(i);
				if ( value.length() > width ) {
			// ...
```

---

## Where to go next

- [JDBC Application Development](Develop-JDBC.md) - the SDK, the live result model, and the SQL you can use.
- [Developing with TLS](Develop-TLS.md) - connect over TLS.
- [Dynamic Data Conventions](Dynamic-Data-Conventions.md) - the field and content model behind the tables you query.
