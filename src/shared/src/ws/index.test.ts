import { describe, it, expect, vi, beforeEach } from "vitest";
import { sha256 } from "js-sha256";
import { WSClient, TerminalSocket, LogsSocket } from "./index.js";

// Minimal WebSocket mock
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static OPEN = 1;
  static CLOSED = 3;
  readyState = MockWebSocket.OPEN;
  binaryType = "blob";
  onopen: ((ev?: any) => void) | null = null;
  onmessage: ((ev: { data: any }) => void) | null = null;
  onclose: ((ev?: any) => void) | null = null;
  onerror: ((ev?: any) => void) | null = null;
  sent: any[] = [];
  closed = false;

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
  }

  send(data: any) {
    this.sent.push(data);
  }

  close() {
    this.closed = true;
    this.readyState = 3;
    if (this.onclose) this.onclose({ code: 1000, reason: "" });
  }

  static reset() {
    MockWebSocket.instances = [];
  }
}

vi.stubGlobal("WebSocket", MockWebSocket);

describe("WSClient", () => {
  beforeEach(() => {
    MockWebSocket.reset();
    vi.useFakeTimers();
  });

  it("connects with token hash in query string", () => {
    const ws = new WSClient();
    ws.connect("ws://localhost:8000/ws", "my-token");
    expect(MockWebSocket.instances.length).toBe(1);
    expect(MockWebSocket.instances[0].url).toContain(`token=${sha256("my-token")}`);
  });

  it("emits open event", () => {
    const ws = new WSClient();
    const handler = vi.fn();
    ws.on("open", handler);
    ws.connect("ws://localhost/ws", "t");
    MockWebSocket.instances[0].onopen!();
    expect(handler).toHaveBeenCalledOnce();
  });

  it("parses and emits typed messages", () => {
    const ws = new WSClient();
    const handler = vi.fn();
    ws.on("image.pull", handler);
    ws.connect("ws://localhost/ws", "t");
    MockWebSocket.instances[0].onmessage!({ data: JSON.stringify({ type: "image.pull", pull_id: "p1", status: "completed" }) });
    expect(handler).toHaveBeenCalledWith(expect.objectContaining({ type: "image.pull", pull_id: "p1" }));
  });

  it("reconnects on close", () => {
    const ws = new WSClient();
    ws.connect("ws://localhost/ws", "t");
    MockWebSocket.instances[0].onclose!();
    expect(MockWebSocket.instances.length).toBe(1);
    vi.advanceTimersByTime(3000);
    expect(MockWebSocket.instances.length).toBe(2);
  });

  it("does not reconnect after manual disconnect", () => {
    const ws = new WSClient();
    ws.connect("ws://localhost/ws", "t");
    ws.disconnect();
    expect(MockWebSocket.instances[0].closed).toBe(true);
    vi.advanceTimersByTime(3000);
    expect(MockWebSocket.instances.length).toBe(1);
  });

  it("send serializes data when open", () => {
    const ws = new WSClient();
    ws.connect("ws://localhost/ws", "t");
    MockWebSocket.instances[0].onopen!();
    ws.send({ action: "ping" });
    expect(MockWebSocket.instances[0].sent[0]).toBe('{"action":"ping"}');
  });
});

describe("TerminalSocket", () => {
  beforeEach(() => {
    MockWebSocket.reset();
  });

  it("connects to /ws/terminal with ticket query param", () => {
    const ts = new TerminalSocket();
    ts.connect("ws://localhost:8000", "ticket abc");
    expect(MockWebSocket.instances[0].url).toBe("ws://localhost:8000/ws/terminal?ticket=ticket%20abc");
  });

  it("connects to a custom path", () => {
    const ts = new TerminalSocket();
    ts.connect("ws://localhost:8000", "t", "/ws/terminal/host");
    expect(MockWebSocket.instances[0].url).toBe("ws://localhost:8000/ws/terminal/host?ticket=t");
  });

  it("uses arraybuffer binary type", () => {
    const ts = new TerminalSocket();
    ts.connect("ws://localhost:8000", "t");
    expect(MockWebSocket.instances[0].binaryType).toBe("arraybuffer");
  });

  it("emits data callback on message", () => {
    const ts = new TerminalSocket();
    const handler = vi.fn();
    ts.on("data", handler);
    ts.connect("ws://localhost:8000", "t");
    MockWebSocket.instances[0].onmessage!({ data: "hello" });
    expect(handler).toHaveBeenCalledWith("hello");
  });

  it("sendInput sends raw data", () => {
    const ts = new TerminalSocket();
    ts.connect("ws://localhost:8000", "t");
    ts.sendInput("ls\n");
    expect(MockWebSocket.instances[0].sent[0]).toBe("ls\n");
  });

  it("resize sends JSON control frame", () => {
    const ts = new TerminalSocket();
    ts.connect("ws://localhost:8000", "t");
    ts.resize(24, 80);
    expect(MockWebSocket.instances[0].sent[0]).toBe('{"type":"resize","rows":24,"cols":80}');
  });

  it("emits close with code and reason", () => {
    const ts = new TerminalSocket();
    const handler = vi.fn();
    ts.on("close", handler);
    ts.connect("ws://localhost:8000", "t");
    MockWebSocket.instances[0].onclose!({ code: 1008, reason: "Invalid ticket" });
    expect(handler).toHaveBeenCalledWith({ code: 1008, reason: "Invalid ticket" });
  });

  it("does not send after disconnect", () => {
    const ts = new TerminalSocket();
    ts.connect("ws://localhost:8000", "t");
    ts.disconnect();
    ts.sendInput("x");
    ts.resize(1, 1);
    expect(MockWebSocket.instances[0].sent.length).toBe(0);
  });
});

describe("LogsSocket", () => {
  beforeEach(() => {
    MockWebSocket.reset();
  });

  it("connects to container logs endpoint with token hash", () => {
    const ls = new LogsSocket();
    ls.connect("ws://localhost:8000", "abc123", "my-token");
    const url = MockWebSocket.instances[0].url;
    expect(url).toContain("/ws/containers/abc123/logs");
    expect(url).toContain(`token=${sha256("my-token")}`);
  });

  it("appends optional query params", () => {
    const ls = new LogsSocket();
    ls.connect("ws://localhost:8000", "c1", "t", { since: 100, follow: true });
    const url = MockWebSocket.instances[0].url;
    expect(url).toContain("since=100");
    expect(url).toContain("follow=true");
    expect(url).not.toContain("until=");
  });

  it("emits raw log lines on data", () => {
    const ls = new LogsSocket();
    const handler = vi.fn();
    ls.on("data", handler);
    ls.connect("ws://localhost:8000", "c1", "t");
    MockWebSocket.instances[0].onmessage!({ data: "log line 1" });
    expect(handler).toHaveBeenCalledWith("log line 1");
  });

  it("disconnect closes socket without close event", () => {
    const ls = new LogsSocket();
    const handler = vi.fn();
    ls.on("close", handler);
    ls.connect("ws://localhost:8000", "c1", "t");
    ls.disconnect();
    expect(MockWebSocket.instances[0].closed).toBe(true);
    expect(handler).not.toHaveBeenCalled();
  });
});
