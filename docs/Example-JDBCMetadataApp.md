# Worked Example: JDBCMetadataApp

`JDBCMetadataApp`, in the SDK, prints the catalogue that a MetaFluent JDBC connection reports through `DatabaseMetaData`: the questions a database browsing tool asks the driver before it runs a query. Point it at a deployment and it lists the catalog, the schemas, the table types, every table you can query and, for the tables that have a fixed set of columns, their columns. It is the quickest way to see what a deployment serves, and a compact example of the catalogue side of the driver.

This page walks through the class section by section. The code below is the actual example, with the less instructive lines elided as `// ...`; the complete file is in the SDK at `examples/src/com/metafluent/examples/metadata/JDBCMetadataApp.java`, and `bin/JDBCMetadataApp.jar` contains it prebuilt.

**Audience:** Java developers who have read [JDBC Application Development](Develop-JDBC.md), and anyone who wants to see a deployment's tables.

---

## Running it

```
java -jar bin/JDBCMetadataApp.jar -host localhost
```

`-port` sets a session server port other than `8900`, and `-user` names the user the connection runs as. `-schema` and `-table` narrow the listing with JDBC LIKE patterns (`%` matches any sequence of characters, `_` any single character); both default to `%`. For example `-schema Quotes -table 'R%'` lists `Quotes.RDF` alone. The program exits with status 0 when the catalogue was listed, and 1 with the failure's message on stderr when it could not connect.

Against the simulator deployment of the [Quick Start](Quick-Start.md) it prints this (the column lists shortened):

```
Connection
  Driver:   MetaFluent 1.1.0
  Database: MetaFluent 6.0.0
  URL:      metafluent://localhost:8900

Catalogs (getCatalogs)
  Default

Schemas (getSchemas): TABLE_SCHEM, TABLE_CATALOG
  Chains            Default
  DatabaseMetadata  Default
  Quotes            Default
  _Functions_       Default

Table types (getTableTypes)
  FUNCTION_TABLE
  TABLE
  VIEW

Tables (getTables, schema '%', table '%'): TABLE_CAT, TABLE_SCHEM, TABLE_NAME, TABLE_TYPE
  Default  _Functions_       MFMath      FUNCTION_TABLE
  Default  _Functions_       MFUtil      FUNCTION_TABLE
  Default  _Functions_       _Intrinsic  FUNCTION_TABLE
  Default  DatabaseMetadata  Columns     TABLE
  Default  DatabaseMetadata  Tables      TABLE
  Default  Quotes            RDF         TABLE
  Default  Chains            RDF         VIEW

Columns (getColumns, schema '%', table '%'): COLUMN_NAME, TYPE_NAME, COLUMN_SIZE
  Default._Functions_.MFMath (FUNCTION_TABLE)
    no columns
  Default.DatabaseMetadata.Tables (TABLE)
    TABLE_ID     STRING  40
    TABLE_CAT    STRING  25
    TABLE_SCHEM  STRING  25
    TABLE_NAME   STRING  80
    TABLE_TYPE   STRING  25
    ...
  Default.Quotes.RDF (TABLE)
    no columns
  Default.Chains.RDF (VIEW)
    no columns

Unsupported call (getPrimaryKeys)
  SQLFeatureNotSupportedException: DatabaseMetaData.getPrimaryKeys is not supported by the MetaFluent driver
```

A market-data table and a chain view report no columns: their fields are those of the [content model](Dynamic-Data-Conventions.md), which can hold thousands, and a query names the ones it wants. The tables with a fixed set of columns, such as `DatabaseMetadata.Tables` here or a table read from a relational database, list them. The server reads a table's columns once, shortly after it starts; a listing taken in the first seconds of a deployment's life can show `no columns` for a table that has them, and shows them on the next run.

---

## 1. Command-line options

The options are declared in the nested `AppOptions` class with the SDK's command-line utilities, the same way `JDBCTestApp` declares its own:

```java
public static class AppOptions extends Options {
	@StringOption(defaultValue = "localhost", description = "Session server host name", flag = "host", required = false)
	public static String Host = "localhost";

	@IntegerOption(defaultValue = 8900, description = "Session server port number", flag = "port", required = false)
	public static int Port = 8900;

	@StringOption(defaultValue = "", description = "User name for the connection", flag = "user", required = false)
	public static String User = "";

	@StringOption(defaultValue = "%", description = "Schema name pattern (JDBC LIKE pattern)", flag = "schema", required = false)
	public static String SchemaPattern = "%";

	@StringOption(defaultValue = "%", description = "Table name pattern (JDBC LIKE pattern)", flag = "table", required = false)
	public static String TablePattern = "%";
}
```

`main()` evaluates the command line first; an unknown option prints the usage and exits with status 1.

---

## 2. Connect and ask

The connection is the standard JDBC pattern. The driver registers itself, so `DriverManager` finds it from the URL; the application name and user travel as connection properties. Everything the program prints comes from the one `DatabaseMetaData` object, in the order a browsing tool asks:

```java
String url = String.format("jdbc:metafluent://%s:%d", AppOptions.Host, AppOptions.Port);
Properties properties = new Properties();
properties.setProperty("com.metafluent.jdbc.application-name", JDBCMetadataApp.class.getName());
properties.setProperty("com.metafluent.jdbc.application-version", "1.0.0");
properties.setProperty("com.metafluent.jdbc.user", AppOptions.User);
try (Connection connection = DriverManager.getConnection(url, properties)) {
	DatabaseMetaData metadata = connection.getMetaData();
	printDriverAndProduct(metadata);
	printCatalogs(metadata);
	printSchemas(metadata);
	printTableTypes(metadata);
	List<String[]> tables = printTables(metadata, AppOptions.SchemaPattern, AppOptions.TablePattern);
	printColumns(metadata, AppOptions.SchemaPattern, AppOptions.TablePattern, tables);
	printUnsupportedCall(metadata, tables);
} catch (SQLException e) {
	System.err.println("JDBCMetadataApp failed: " + e.getMessage());
	System.exit(1);
}
```

Each catalogue call answers at once with a complete snapshot and runs no statement, so the whole program is a single round of questions and the connection closes when the block ends.

---

## 3. The tables

`getTables` takes the catalog, a schema pattern, a table pattern and the types wanted; `null` for the types lists every type. The rows read are kept, in the driver's order, because the column listing groups by them:

```java
static List<String[]> printTables(DatabaseMetaData metadata, String schemaPattern, String tablePattern)
		throws SQLException {
	// ...
	try (ResultSet tableRows = metadata.getTables(null, schemaPattern, tablePattern, null)) {
		tables = readRows(tableRows, "TABLE_CAT", "TABLE_SCHEM", "TABLE_NAME", "TABLE_TYPE");
	}
	printRows(tables, "  ");
	return tables;
}
```

`TABLE_TYPE` is `TABLE` for a table, `VIEW` for a view (a `CREATE VIEW` view or the chain view of a market-data table) and `FUNCTION_TABLE` for a function library, as [Browsing the tables](Develop-JDBC.md#browsing-the-tables) describes.

---

## 4. The columns, grouped by table

One `getColumns` call with the same patterns and `%` for the column pattern answers every column of every matching table. The program groups the rows by their table's qualified name and prints them under each table listed by `getTables`, with `no columns` for a table that reported none:

```java
try (ResultSet columnRows = metadata.getColumns(null, schemaPattern, tablePattern, "%")) {
	while (columnRows.next()) {
		String qualifiedTableName = qualifiedTableName(columnRows.getString("TABLE_CAT"),
				columnRows.getString("TABLE_SCHEM"), columnRows.getString("TABLE_NAME"));
		// ... collect COLUMN_NAME, TYPE_NAME, COLUMN_SIZE under qualifiedTableName
	}
}
for (String[] table : tables) {
	// ... print the table's heading, then its columns or "no columns"
}
```

---

## 5. A call the driver does not support

The `DatabaseMetaData` calls that return a result set and that MetaFluent does not implement, such as `getPrimaryKeys` and `getIndexInfo`, throw `SQLFeatureNotSupportedException`. The program asks one of them, for the first table listed, and prints the exception's message so you can see what a tool meets:

```java
try (ResultSet primaryKeys = metadata.getPrimaryKeys(null, schema, tableName)) {
	printRows(readRows(primaryKeys, "COLUMN_NAME", "KEY_SEQ", "PK_NAME"), "  ");
} catch (SQLFeatureNotSupportedException e) {
	System.out.println("  SQLFeatureNotSupportedException: " + e.getMessage());
}
```

---

## Where to go next

- [JDBC Application Development](Develop-JDBC.md) - the SDK, the live result model, the SQL you can use and browsing the tables.
- [Worked Example: JDBCTestApp](Example-JDBCTestApp.md) - running a query and keeping a live table on screen.
- [Dynamic Data Conventions](Dynamic-Data-Conventions.md) - the field and content model behind the tables that report no columns.
