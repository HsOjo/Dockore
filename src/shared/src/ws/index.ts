import { sha256 } from "js-sha256";

export class WSClient {
  private ws: WebSocket | null = null;
  private url = "";
  private token = "";
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private listeners: Map<string, Array<(data: any) => void>> = new Map();
  private isManualClose = false;

  connect(url: string, token: string) {
    this.url = url;
    this.token = token;
    this.isManualClose = false;
    this._connect();
  }

  private _connect() {
    if (this.ws) return;
    try {
      const fullUrl = `${this.url}?token=${encodeURIComponent(sha256(this.token))}`;
      this.ws = new WebSocket(fullUrl);
      this.ws.onopen = () => {
        this.emit("open", {});
      };
      this.ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          this.emit(data.type || "message", data);
        } catch {
          this.emit("message", ev.data);
        }
      };
      this.ws.onclose = () => {
        this.ws = null;
        this.emit("close", {});
        if (!this.isManualClose) {
          this.reconnectTimer = setTimeout(() => this._connect(), 3000);
        }
      };
      this.ws.onerror = () => {
        this.emit("error", {});
      };
    } catch {
      this.reconnectTimer = setTimeout(() => this._connect(), 3000);
    }
  }

  disconnect() {
    this.isManualClose = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  on(type: string, handler: (data: any) => void) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type)!.push(handler);
  }

  off(type: string, handler: (data: any) => void) {
    const arr = this.listeners.get(type);
    if (arr) {
      const idx = arr.indexOf(handler);
      if (idx >= 0) arr.splice(idx, 1);
    }
  }

  private emit(type: string, data: any) {
    const arr = this.listeners.get(type);
    if (arr) {
      for (const h of arr) {
        try {
          h(data);
        } catch {
          // ignore
        }
      }
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

export class TerminalSocket {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Array<(data: any) => void>> = new Map();

  connect(url: string, ticket: string) {
    this.disconnect();
    const fullUrl = `${url}/ws/terminal?ticket=${encodeURIComponent(ticket)}`;
    this.ws = new WebSocket(fullUrl);
    this.ws.binaryType = "arraybuffer";
    this.ws.onopen = () => this.emit("open", {});
    this.ws.onmessage = (ev) => this.emit("data", ev.data);
    this.ws.onclose = (ev) => {
      this.ws = null;
      this.emit("close", { code: ev.code, reason: ev.reason });
    };
    this.ws.onerror = () => this.emit("error", {});
  }

  disconnect() {
    if (this.ws) {
      const ws = this.ws;
      this.ws = null;
      ws.onclose = null;
      ws.close();
    }
  }

  sendInput(data: string | ArrayBuffer) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(data);
    }
  }

  resize(rows: number, cols: number) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: "resize", rows, cols }));
    }
  }

  get connected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  on(type: string, handler: (data: any) => void) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type)!.push(handler);
  }

  off(type: string, handler: (data: any) => void) {
    const arr = this.listeners.get(type);
    if (arr) {
      const idx = arr.indexOf(handler);
      if (idx >= 0) arr.splice(idx, 1);
    }
  }

  private emit(type: string, data: any) {
    const arr = this.listeners.get(type);
    if (arr) {
      for (const h of arr) {
        try {
          h(data);
        } catch {
          // ignore
        }
      }
    }
  }
}

export interface LogsSocketParams {
  since?: string | number;
  until?: string | number;
  follow?: boolean;
}

export class LogsSocket {
  private ws: WebSocket | null = null;
  private listeners: Map<string, Array<(data: any) => void>> = new Map();

  connect(url: string, containerId: string, token: string, params: LogsSocketParams = {}) {
    this.connectPath(url, `/ws/containers/${encodeURIComponent(containerId)}/logs`, token, params);
  }

  connectPath(url: string, path: string, token: string, params: LogsSocketParams = {}) {
    this.disconnect();
    const query = new URLSearchParams();
    query.set("token", sha256(token));
    if (params.since !== undefined) query.set("since", String(params.since));
    if (params.until !== undefined) query.set("until", String(params.until));
    if (params.follow !== undefined) query.set("follow", params.follow ? "true" : "false");
    const fullUrl = `${url}${path}?${query.toString()}`;
    this.ws = new WebSocket(fullUrl);
    this.ws.binaryType = "arraybuffer";
    this.ws.onopen = () => this.emit("open", {});
    this.ws.onmessage = (ev) => this.emit("data", ev.data);
    this.ws.onclose = (ev) => {
      this.ws = null;
      this.emit("close", { code: ev.code, reason: ev.reason });
    };
    this.ws.onerror = () => this.emit("error", {});
  }

  disconnect() {
    if (this.ws) {
      const ws = this.ws;
      this.ws = null;
      ws.onclose = null;
      ws.close();
    }
  }

  get connected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  on(type: string, handler: (data: any) => void) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type)!.push(handler);
  }

  off(type: string, handler: (data: any) => void) {
    const arr = this.listeners.get(type);
    if (arr) {
      const idx = arr.indexOf(handler);
      if (idx >= 0) arr.splice(idx, 1);
    }
  }

  private emit(type: string, data: any) {
    const arr = this.listeners.get(type);
    if (arr) {
      for (const h of arr) {
        try {
          h(data);
        } catch {
          // ignore
        }
      }
    }
  }
}

export const wsClient = new WSClient();
