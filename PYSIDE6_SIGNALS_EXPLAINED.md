# How PySide6 Signals and Slots Work

## Overview

PySide6 uses Qt's **signal-slot mechanism** for communication between objects. This is a type-safe, decoupled way for objects to communicate without knowing about each other directly.

## Key Concepts

### 1. **Signal Definition**
Signals are declared as class attributes using `Signal()`:

```python
class DetectionParametersWidget(QWidget):
    particlesUpdated = Signal(object)  # Signal that carries a DataFrame
    openTrajectoryLinking = Signal()   # Signal with no arguments
    parameter_changed = Signal()        # Signal with no arguments
```

### 2. **Signal Emission**
When something happens, you emit the signal:

```python
# In DetectionParametersWidget.save_params()
self.config_manager.save_detection_params(params)
self.parameter_changed.emit()  # Emit the signal here
```

### 3. **Signal Connection**
Other objects connect their methods (slots) to your signals:

```python
# In ParticleDetectionWindow.setup_ui()
self.main_layout.right_panel.parameter_changed.connect(
    self.clear_processed_data  # This method will be called
)
```

## How PySide6 Processes Signals

### The Event Loop

PySide6 runs an **event loop** (via `QApplication.exec()`) that continuously processes events. Here's how signals work:

1. **Signal Emission**: When `signal.emit()` is called, Qt doesn't immediately call the connected slots. Instead, it:
   - Creates a **signal event** 
   - Posts it to the **event queue**
   - Returns immediately (non-blocking)

2. **Event Processing**: The event loop processes events in order:
   - UI events (mouse clicks, key presses)
   - Timer events
   - **Signal events** (your custom signals)
   - Paint events
   - etc.

3. **Slot Invocation**: When the event loop processes a signal event:
   - It looks up all connected slots
   - Calls each connected slot with the signal's arguments
   - Slots execute in the order they were connected

### Example Flow from Your Codebase

```python
# 1. Signal is defined
class DetectionParametersWidget(QWidget):
    parameter_changed = Signal()

# 2. Signal is connected to a slot
# In ParticleDetectionWindow.setup_ui()
self.main_layout.right_panel.parameter_changed.connect(
    self.clear_processed_data
)

# 3. Signal is emitted (in DetectionParametersWidget.save_params())
self.parameter_changed.emit()

# 4. Event loop processes the signal event
# 5. clear_processed_data() is called automatically
```

## Connection Types

### Direct Connection (Synchronous)
```python
# Slot is called immediately, in the same thread
signal.connect(slot, Qt.ConnectionType.DirectConnection)
```

### Queued Connection (Asynchronous) - Default for cross-thread
```python
# Signal event is queued, slot called later in event loop
signal.connect(slot, Qt.ConnectionType.QueuedConnection)
```

### Auto Connection (Default)
```python
# Qt chooses: Direct if same thread, Queued if different threads
signal.connect(slot)  # Auto connection (default)
```

## Thread Safety

### Same Thread (Main UI Thread)
- Signals are processed **synchronously** in the same call stack
- Slot is called immediately when signal is emitted
- This is the default behavior in single-threaded applications

### Different Threads
- Signals are **queued** and processed asynchronously
- The slot runs in the receiver's thread
- This is automatic when connecting signals across threads

Example from your codebase:
```python
# In services.py - QThread emits signals
class FindParticlesThread(QThread):
    processing_frame = Signal(str)
    finished = Signal()
    
    def run(self):
        # This runs in a worker thread
        self.processing_frame.emit("Processing frame 1")
        # Signal is queued, processed in main thread's event loop
```

## How the Receiver "Knows"

The receiver doesn't actively "know" - instead:

1. **Connection Registration**: When you call `.connect()`, Qt registers the connection in an internal table:
   ```
   Signal Object → List of Connected Slots
   ```

2. **Signal Emission**: When `.emit()` is called, Qt:
   - Looks up the signal in the connection table
   - Creates events for each connected slot
   - Posts events to the event queue

3. **Event Processing**: The event loop (running in `QApplication.exec()`):
   - Processes the signal event
   - Calls the registered slot function
   - Passes any signal arguments to the slot

## Visual Flow

```
[Signal Emitter]
     |
     | emit()
     v
[Qt Signal System]
     |
     | Creates signal event
     v
[Event Queue]
     |
     | Event loop processes
     v
[Qt Signal System]
     |
     | Looks up connections
     v
[Connected Slots]
     |
     | Calls slot functions
     v
[Slot Receivers]
```

## Practical Example from Your Code

```python
# Step 1: Define signal
class DetectionParametersWidget(QWidget):
    particlesUpdated = Signal(object)  # Carries a DataFrame

# Step 2: Connect signal to slot
# In ParticleDetectionWindow.setup_ui()
self.main_layout.right_panel.particlesUpdated.connect(
    self.on_particles_updated  # Method to call
)

# Step 3: Emit signal with data
# In DetectionParametersWidget
all_particles_df = self._load_all_particles_df()
self.particlesUpdated.emit(all_particles_df)  # Emit with DataFrame

# Step 4: Slot receives the data
# In ParticleDetectionWindow
def on_particles_updated(self, particle_data):
    # particle_data is the DataFrame that was emitted
    if self.frame_player:
        self.frame_player.display_frame(...)
```

## Key Points

1. **Non-blocking**: Signal emission returns immediately; slots run later via event loop
2. **Decoupled**: Emitter doesn't know who's listening; receiver doesn't know who emitted
3. **Type-safe**: Signal signatures are checked at connection time
4. **Thread-safe**: Automatic queuing for cross-thread communication
5. **Multiple receivers**: One signal can be connected to multiple slots
6. **Event-driven**: Everything happens through the event loop

## Why This Design?

1. **Decoupling**: Objects don't need direct references to each other
2. **Flexibility**: Easy to add/remove connections at runtime
3. **Thread Safety**: Automatic handling of cross-thread communication
4. **Performance**: Events are batched and processed efficiently
5. **Maintainability**: Clear separation of concerns

## Debugging Signals

You can verify connections:
```python
# Check if signal is connected
if signal.receivers(signal) > 0:
    print("Signal has receivers")

# Disconnect all
signal.disconnect()

# Disconnect specific slot
signal.disconnect(slot_function)
```

## Summary

**The receiver "knows" because:**
1. The connection was registered when `.connect()` was called
2. Qt's event loop processes signal events
3. The event loop looks up registered connections and calls the slots
4. This all happens automatically - you just emit signals and connect slots!

The magic is in Qt's **meta-object system** and **event loop**, which handle all the connection tracking and slot invocation behind the scenes.

