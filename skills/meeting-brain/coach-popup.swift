#!/usr/bin/env swift
// coach-popup.swift — live Meeting Coach overlay (macOS)
//
// A tiny menu-bar app (⚡) that tails the meeting-brain log and shows the latest
// coaching / strategic flags in a floating panel, color-coded:
//   orange = prescriptive nudge (→)   green = positive (✓)   grey = session header (===)
// The panel floats over everything and pulses the menu-bar icon on a new flag,
// so you get a glanceable co-pilot while you're actually in the meeting.
//
// Build:   swiftc -O coach-popup.swift -o Coach   &&   ./Coach
// Or run directly (no build):   swift coach-popup.swift > /dev/null 2>&1 &
// Stop:    pkill -f coach-popup     (or "Quit" from the ⚡ menu)
//
// Log path: reads $MEETING_BRAIN_LOG, else /tmp/meeting-brain.log.
// Must match the LOG constant in meeting-brain.py.

import AppKit
import Foundation

class AppDelegate: NSObject, NSApplicationDelegate {
    var statusItem: NSStatusItem!
    var panel: NSPanel!
    var textView: NSTextView!
    var logPosition: Int64 = 0   // set to EOF on launch so stale content is skipped
    var timer: Timer?
    var recentLines: [String] = []
    let maxVisible = 12
    let logFile = ProcessInfo.processInfo.environment["MEETING_BRAIN_LOG"] ?? "/tmp/meeting-brain.log"

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupMenuBar()
        setupPanel()
        // Skip past any existing log content so stale entries aren't shown on launch
        if let attrs = try? FileManager.default.attributesOfItem(atPath: logFile),
           let size = attrs[.size] as? Int64 {
            logPosition = size
        }
        startPolling()
        NSApp.activate(ignoringOtherApps: true)
        panel.orderFrontRegardless()
    }

    // MARK: — Menu bar

    func setupMenuBar() {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let btn = statusItem.button {
            btn.title = "⚡"
            btn.font = NSFont.systemFont(ofSize: 13)
            btn.toolTip = "Meeting Coach — click to show/hide"
            btn.action = #selector(togglePanel)
            btn.target = self
        }
        // Right-click menu
        let menu = NSMenu()
        menu.addItem(withTitle: "Show / Hide", action: #selector(togglePanel), keyEquivalent: "")
        menu.addItem(.separator())
        menu.addItem(withTitle: "Quit Coach", action: #selector(quitApp), keyEquivalent: "")
        statusItem.menu = nil  // left click uses action; right click handled below
        // To support both left-click (toggle) and right-click (menu), swap menu on right click
        statusItem.button?.sendAction(on: [.leftMouseUp, .rightMouseUp])
    }

    @objc func togglePanel() {
        let event = NSApp.currentEvent
        if event?.type == .rightMouseUp {
            showMenu()
            return
        }
        if panel.isVisible {
            panel.orderOut(nil)
        } else {
            panel.orderFrontRegardless()
        }
    }

    func showMenu() {
        let menu = NSMenu()
        let toggleTitle = panel.isVisible ? "Hide Panel" : "Show Panel"
        menu.addItem(withTitle: toggleTitle, action: #selector(togglePanelFromMenu), keyEquivalent: "")
        menu.addItem(.separator())
        menu.addItem(withTitle: "Quit Coach", action: #selector(quitApp), keyEquivalent: "")
        menu.items.forEach { $0.target = self }
        statusItem.menu = menu
        statusItem.button?.performClick(nil)
        statusItem.menu = nil  // reset so left-click uses action next time
    }

    @objc func togglePanelFromMenu() {
        if panel.isVisible { panel.orderOut(nil) } else { panel.orderFrontRegardless() }
    }

    @objc func quitApp() { NSApp.terminate(nil) }

    // MARK: — Panel

    func setupPanel() {
        let width: CGFloat = 820
        let height: CGFloat = 380
        // Bottom-right corner, above Dock — visible regardless of other windows
        let screen = NSScreen.screens.first?.visibleFrame ?? NSScreen.main?.visibleFrame ?? .zero
        let origin = NSPoint(x: screen.maxX - width - 20, y: screen.minY + 20)

        panel = NSPanel(
            contentRect: NSRect(origin: origin, size: NSSize(width: width, height: height)),
            styleMask: [.titled, .closable, .resizable, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        panel.title = "⚡ Meeting Coach"
        panel.level = .floating
        panel.collectionBehavior = [.canJoinAllSpaces, .fullScreenAuxiliary]
        panel.isMovableByWindowBackground = true
        panel.appearance = NSAppearance(named: .darkAqua)
        panel.backgroundColor = NSColor(red: 0.08, green: 0.08, blue: 0.10, alpha: 1.0)
        panel.isOpaque = true
        panel.hasShadow = true
        panel.alphaValue = 0.95
        panel.delegate = self

        let scroll = NSScrollView(frame: NSRect(x: 0, y: 0, width: width, height: height - 30))
        scroll.autoresizingMask = [.width, .height]
        scroll.hasVerticalScroller = true
        scroll.hasHorizontalScroller = false
        scroll.drawsBackground = false

        textView = NSTextView(frame: scroll.bounds)
        textView.isEditable = false
        textView.isSelectable = false
        textView.backgroundColor = .clear
        textView.textContainerInset = NSSize(width: 10, height: 8)
        // Make text reflow to the panel's current width and grow vertically (so resizing actually widens the content)
        textView.minSize = NSSize(width: 0, height: 0)
        textView.maxSize = NSSize(width: CGFloat.greatestFiniteMagnitude, height: CGFloat.greatestFiniteMagnitude)
        textView.isVerticallyResizable = true
        textView.isHorizontallyResizable = false
        textView.autoresizingMask = [.width]
        textView.textContainer?.widthTracksTextView = true
        textView.textContainer?.containerSize = NSSize(width: scroll.contentSize.width, height: CGFloat.greatestFiniteMagnitude)

        scroll.documentView = textView
        panel.contentView?.addSubview(scroll)

        render(["Ready — start a session to see coaching nudges"])
    }

    // MARK: — Log polling

    func startPolling() {
        timer = Timer.scheduledTimer(withTimeInterval: 3, repeats: true) { [weak self] _ in self?.poll() }
    }

    func poll() {
        guard let attrs = try? FileManager.default.attributesOfItem(atPath: logFile),
              let size = attrs[.size] as? Int64 else { return }

        // Log was truncated — new session started. Clear display and read from beginning.
        if size < logPosition {
            logPosition = 0
            recentLines.removeAll()
            DispatchQueue.main.async { self.render(self.recentLines) }
        }

        guard size > logPosition else { return }

        guard let fh = FileHandle(forReadingAtPath: logFile) else { return }
        fh.seek(toFileOffset: UInt64(logPosition))
        let data = fh.readDataToEndOfFile()
        fh.closeFile()
        logPosition = size

        guard let text = String(data: data, encoding: .utf8) else { return }
        let newLines = text.components(separatedBy: "\n")
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty && $0 != "." }

        guard !newLines.isEmpty else { return }

        recentLines.append(contentsOf: newLines)
        if recentLines.count > maxVisible * 4 { recentLines.removeFirst(recentLines.count - maxVisible * 4) }

        DispatchQueue.main.async {
            self.render(self.recentLines)
            self.flash()
            // Pulse menu bar icon on alert so you notice even when panel is hidden
            if !self.panel.isVisible {
                self.pulseMenuBarIcon()
            }
        }
    }

    // MARK: — Display

    func color(for line: String) -> NSColor {
        if line.contains("→") {
            return NSColor(red: 1.0, green: 0.60, blue: 0.0, alpha: 1)   // orange — prescriptive nudge
        }
        if line.contains("✓") {
            return NSColor(red: 0.20, green: 0.84, blue: 0.36, alpha: 1) // green — positive
        }
        if line.hasPrefix("===") {
            return NSColor(white: 0.45, alpha: 1)                         // grey — session header
        }
        return NSColor(white: 0.72, alpha: 1)
    }

    func render(_ lines: [String]) {
        let attr = NSMutableAttributedString()
        let font = NSFont.monospacedSystemFont(ofSize: 11, weight: .regular)
        for line in lines.suffix(maxVisible).reversed() {
            // No char cap — let the text view wrap the full line to the panel's current width
            attr.append(NSAttributedString(
                string: line + "\n",
                attributes: [.foregroundColor: color(for: line), .font: font]
            ))
        }
        textView.textStorage?.setAttributedString(attr)
    }

    func flash() {
        panel.alphaValue = 1.0
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.35) { self.panel.alphaValue = 0.95 }
    }

    func pulseMenuBarIcon() {
        // Briefly change icon to signal a new alert when panel is hidden
        statusItem.button?.title = "⚠"
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) {
            self.statusItem.button?.title = "⚡"
        }
    }
}

// Panel close button = hide only, not quit
extension AppDelegate: NSWindowDelegate {
    func windowShouldClose(_ sender: NSWindow) -> Bool {
        panel.orderOut(nil)   // just hide
        return false          // don't close/destroy
    }
}

let app = NSApplication.shared
app.setActivationPolicy(.regular)   // show dock icon — required for window to appear when launched as script
let delegate = AppDelegate()
app.delegate = delegate
app.run()
