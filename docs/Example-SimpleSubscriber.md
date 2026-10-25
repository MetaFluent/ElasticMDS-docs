# Worked Example: SimpleSubscriber

`SimpleSubscriber`, in the SDK, is the canonical form of a MetaFluent JMS subscriber. Nearly every subscribing application follows this pattern, and it is deliberately small - it uses only the standard `javax.jms` API, with nothing MetaFluent-specific beyond the connection factory and the [Dynamic Data Conventions](Dynamic-Data-Conventions.md) used to read messages. Compared with a typical market-data application it is trivial.

This page walks through the class section by section. The code below is the actual example; the complete file, with its imports and the `AppOptions` command-line class, is in the SDK at `examples/src/com/metafluent/examples/simplesub/SimpleSubscriber.java`.

**Audience:** developers new to MetaFluent JMS.

---

## The class

`SimpleSubscriber` implements two JMS callback interfaces: `MessageListener` (to receive messages) and `ExceptionListener` (to hear about connection-level failures). One instance holds the connection, the session, and a map of the active subscribers.

```java
public class SimpleSubscriber implements ExceptionListener, MessageListener {

    private TopicConnectionFactory fTopicConnectionFactory = null;
    private TopicConnection fTopicConnection = null;
    protected TopicSession fTopicSession = null;
    protected Hashtable<String, TopicSubscriber> fSubscribers = new Hashtable<String, TopicSubscriber>();
    private String fUser = null;
    private String fPassword = null;

    public SimpleSubscriber(TopicConnectionFactory factory, String user, String password) {
        fTopicConnectionFactory = factory;
        fUser = user;
        fPassword = password;
    }
```

---

## 1. Initialize the connection and session

`initialize()` sets the application name and the context, creates a connection, registers the exception listener, opens a session, subscribes to the requested topics, and starts the connection. The only MetaFluent-specific step is setting the context; the rest is ordinary JMS.

```java
    public boolean initialize() throws JMSException, JMSSecurityException {
        Properties.ApplicationName = SimpleSubscriber.class.getName();
        Properties.ApplicationVersion = "1.0.0";
        // Set the application context the server uses to allocate a session for this application
        System.setProperty(Properties.ContextNamePropertyName, AppOptions.ContextName);
        // Usually there is one topic connection in an application
        try {
            fTopicConnection = fTopicConnectionFactory.createTopicConnection(fUser, fPassword);
        } catch (JMSSecurityException ex1) {
            System.err.println("Authentication error: " + ex1.getMessage());
            cleanUp();
        } catch (JMSException ex2) {
            // exception handler is not registered yet, so onException will not be called
            System.err.println("Error initializing connection: " + ex2.getMessage());
            cleanUp();
            return false;
        }
        // Register an exception handler
        fTopicConnection.setExceptionListener(this);
        // Create a topic session (usually one per application)
        fTopicSession = fTopicConnection.createTopicSession(false, DynamicDataConventions.NO_ACKNOWLEDGE);
        // Subscribe to one or more topics
        for (String topic : AppOptions.Topics) {
            subscribe(topic);
        }
        // The connection will allocate threads to handle I/O
        fTopicConnection.start();
        return true;
    }
```

---

## 2. Subscribe to a topic

`subscribe()` acquires a `Topic` by name, creates a subscriber (passing the optional selector), registers this class as the message listener, and keeps a reference. Calling `createTopic` / `createSubscriber` again for the same name returns the same objects.

```java
    public void subscribe(String topicName) throws JMSException {
        // Acquire a topic by name
        Topic topic = fTopicSession.createTopic(topicName);
        // Create a subscriber
        TopicSubscriber subscriber = fTopicSession.createSubscriber(topic, AppOptions.Selector, true);
        // Register a message listener
        subscriber.setMessageListener(this);
        // Retain the subscriber for future reference
        fSubscribers.put(topicName, subscriber);
    }
```

---

## 3. Receive and dispatch messages

Messages arrive on `onMessage()`. Content is delivered as `MapMessage`s; the application reads the message type from a property and dispatches on it. See [Dynamic Data Conventions](Dynamic-Data-Conventions.md) for the types.

```java
    public void onMessage(Message msg) {
        // This application is expecting only MapMessages
        if (!(msg instanceof MapMessage)) return;
        try {
            Topic topic = (Topic) msg.getJMSDestination();
            MapMessage map = (MapMessage) msg;
            MsgType type = MsgType.type(msg.getByteProperty(DynamicDataConventions.MSG_TYPE_PROPERTY_NAME));
            switch (type) {
            case CORRECTION:
            case RESET:
            case UPDATE:
                processUpdate(topic, type, map);
                break;
            case IMAGE:
                processImage(topic, map);
                break;
            case STATUS:
                processStatus(topic, map);
                break;
            case STREAM_UPDATE:
                // Ordered multi-stream topics; not used by this application
                break;
            default:
                System.err.println("Unknown message type: " + type);
            }
        } catch (JMSException e) {
            e.printStackTrace();
        }
    }
```

---

## 4. Process an image or an update

An image carries the full set of current field values; an update carries the fields that changed. Both are read the same way - iterate the map's field names and read each value.

```java
    protected void processImage(Topic topic, MapMessage map) throws JMSException {
        synchronized (fUser) {
            System.err.println("Image:" + topic.getTopicName());
            processStatus(topic, map);          // check the data condition
            Enumeration<?> names = map.getMapNames();
            while (names.hasMoreElements()) {
                String name = (String) names.nextElement();
                System.err.printf("%15s: %s\n", name, map.getString(name));
            }
        }
    }

    protected void processUpdate(Topic topic, MsgType type, MapMessage map) throws JMSException {
        synchronized (fUser) {
            System.err.println(type + ": " + topic.getTopicName());
            Enumeration<?> names = map.getMapNames();
            while (names.hasMoreElements()) {
                String name = (String) names.nextElement();
                System.err.printf("%15s: %s\n", name, map.getString(name));
            }
        }
    }
```

---

## 5. Process a status

A status message carries a state code. This application reports it and closes the subscriber on the terminal states (`CLOSED`, `DENIED`, `INVALID`).

```java
    protected void processStatus(Topic topic, MapMessage map) throws JMSException {
        StateCode state = StateCode.code(map.getByteProperty(DynamicDataConventions.STATE_PROPERTY_NAME));
        String text = map.getStringProperty(DynamicDataConventions.TEXT_PROPERTY_NAME);
        synchronized (fUser) {
            switch (state) {
            case OK:
                System.err.println("Data for topic " + topic.getTopicName() + " is OK: " + text);
                break;
            case STALE:
                System.err.println("Data for topic " + topic.getTopicName() + " is stale: " + text);
                break;
            case CLOSED:
                System.err.println("Topic closed: " + topic.getTopicName() + " - " + text);
                fSubscribers.remove(topic.getTopicName()).close();
                break;
            case DENIED:
                System.err.println("Access denied for topic: " + topic.getTopicName() + " - " + text);
                fSubscribers.remove(topic.getTopicName()).close();
                break;
            case INVALID:
                System.err.println("Invalid request for topic: " + topic.getTopicName() + " - " + text);
                fSubscribers.remove(topic.getTopicName()).close();
                break;
            default:
                break;
            }
        }
    }
```

---

## 6. Release resources and handle connection errors

`cleanUp()` closes the session and connection. `onException()` is the connection thread's last act on failure: it cleans up, re-initializes (which creates a new connection and thread), and re-subscribes, so the application recovers on its own.

```java
    public void cleanUp() {
        try {
            if (fTopicSession != null) fTopicSession.close();
        } catch (JMSException e) { }
        fSubscribers.clear();
        try {
            if (fTopicConnection != null) fTopicConnection.close();
        } catch (JMSException e) { }
        fTopicConnection = null;
        fTopicSession = null;
    }

    public void onException(JMSException e) {
        cleanUp();
        System.err.println("Retrying after connection error: " + e);
        try {
            while (!initialize())
                ; // connection timed out before the exception listener registered; force retry
            System.err.println("Reconnected");
        } catch (JMSSecurityException e1) {
            System.err.println("Fatal connection error: " + e1);
            return;
        } catch (JMSException e1) {
            // reconnect failed; onException() will be called again, let it try again
            System.err.println("Error initializing: " + e1.getMessage());
            return;
        }
        // Re-subscribe to the topic list
        for (String topicName : AppOptions.Topics) {
            try {
                subscribe(topicName);
            } catch (Exception e1) {
                System.err.println("Error subscribing to " + topicName);
            }
        }
    }
```

---

## 7. main()

`main()` parses the command-line options, builds the connection factory from the connect specification, constructs the subscriber, and initializes it.

```java
    public static void main(String[] args) {
        AppOptions options = new AppOptions();
        try {
            options.evaluate(args);     // -connect, -context, -user, -password, -selector, topics
        } catch (Exception e) {
            options.printUsage(System.err);
            System.exit(-1);
        }
        SimpleSubscriber app = null;
        try {
            Properties.ApplicationName = SimpleSubscriber.class.getName();
            Properties.ApplicationVersion = "1.0.0";
            System.setProperty(Properties.ContextNamePropertyName, AppOptions.ContextName);
            // Create the MetaFluent-specific topic connection factory
            TopicConnectionFactory connectionFactory = new JavaxTopicConnectionFactory(AppOptions.Connect);
            app = new SimpleSubscriber(connectionFactory, AppOptions.User, AppOptions.Password);
            while (!app.initialize())
                ; // connection timed out before the exception listener registered; force retry
        } catch (JMSSecurityException e) {
            System.err.println("Security error during initialization: " + e.getMessage());
            System.exit(-1);
        } catch (JMSException e) {
            System.err.println("Error initializing application: " + e.getMessage());
            e.printStackTrace();
            System.exit(-1);
        }
    }
```

To run it, see the invocation in [JMS Application Development](Develop-JMS.md).

---

## Where to go next

- [JMS Application Development](Develop-JMS.md) - contexts, addressing, and selectors.
- [Dynamic Data Conventions](Dynamic-Data-Conventions.md) - interpreting the messages this example receives.
