import axios, { AxiosInstance } from 'axios';

// --- Type Definitions ---

export interface SDKConfig {
  baseUrl: string;
  username?: string;
  password?: string;
}

export interface TrackResponse {
  status: string;
  event_id: number;
  message?: string;
}

export interface SchemaRegistration {
  event_name: string;
  version: number;
  json_schema: Record<string, any>;
}

export interface CustomerProfile {
  id: string;
  primary_email: string | null;
  primary_phone: string | null;
  attributes: Record<string, any>;
  timeline: Array<any>;
}

// --- Internal Client Manager ---

class HorizonCore {
  private client: AxiosInstance;
  private token: string | null = null;
  private config: SDKConfig;

  constructor(config: SDKConfig) {
    this.config = config;
    const baseUrl = config.baseUrl.replace(/\/$/, '');
    
    this.client = axios.create({
      baseURL: baseUrl,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  async authenticate(): Promise<void> {
    if (!this.config.username || !this.config.password) {
      throw new Error('[Horizon 360] Missing authentication credentials in config.');
    }

    try {
      const response = await this.client.post('/api/token/', {
        username: this.config.username,
        password: this.config.password,
      });

      if (response.status === 200 && response.data.access) {
        this.token = response.data.access;
        this.client.defaults.headers.common['Authorization'] = `Bearer ${this.token}`;
      } else {
        throw new Error('Invalid token response structure.');
      }
    } catch (error: any) {
      const status = error.response?.status || 'Unknown';
      throw new Error(`[Horizon 360] Authentication failed with status ${status}. Verify credentials.`);
    }
  }

  async registerSchema(eventName: string, jsonSchema: Record<string, any>, version: number = 1): Promise<SchemaRegistration> {
    const response = await this.client.post('/api/schemas/', {
      event_name: eventName,
      version,
      json_schema: jsonSchema,
    });
    return response.data;
  }

  async track(eventName: string, payload: Record<string, any>, schemaVersion: number = 1): Promise<TrackResponse> {
    const response = await this.client.post('/api/events/', {
      event_name: eventName,
      schema_version: schemaVersion,
      raw_payload: payload,
    });
    return response.data;
  }

  async getCustomer(email: string): Promise<CustomerProfile[]> {
    const response = await this.client.get('/api/customers/', {
      params: { email },
    });
    return response.data;
  }
}

// --- Global Module State ---

let defaultInstance: HorizonCore | null = null;

function getClient(): HorizonCore {
  if (!defaultInstance) {
    throw new Error('[Horizon 360] SDK not initialized. Call initializeApp() before utilizing SDK methods.');
  }
  return defaultInstance;
}

// --- Public API Exports ---

/**
 * Initializes the Horizon 360 SDK and establishes the JWT session.
 * Must be called once at application startup.
 */
export async function initializeApp(config: SDKConfig): Promise<void> {
  if (defaultInstance) {
    console.warn('[Horizon 360] SDK is already initialized.');
    return;
  }
  
  const instance = new HorizonCore(config);
  await instance.authenticate();
  defaultInstance = instance;
}

/**
 * Registers a new event structure framework within the Schema Registry.
 */
export async function registerSchema(eventName: string, jsonSchema: Record<string, any>, version: number = 1): Promise<SchemaRegistration> {
  return getClient().registerSchema(eventName, jsonSchema, version);
}

/**
 * Streams an event payload directly into the ingestion firehose.
 */
export async function track(eventName: string, payload: Record<string, any>, schemaVersion: number = 1): Promise<TrackResponse> {
  return getClient().track(eventName, payload, schemaVersion);
}

/**
 * Looks up a unified customer profile from the identity engine.
 */
export async function getCustomer(email: string): Promise<CustomerProfile[]> {
  return getClient().getCustomer(email);
}