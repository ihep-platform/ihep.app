import bcrypt from 'bcryptjs'
import fs from 'fs/promises'
import path from 'path'

export type MockUser = {
  id: number
  username: string
  password: string
  email: string
  firstName: string
  lastName: string
  role: string
  profilePicture?: string | null
  phone?: string | null
  preferredContactMethod?: string | null
  createdAt: Date
}

type PersistedUser = Omit<MockUser, 'createdAt'> & { createdAt: string }

const DATA_PATH = path.join(process.cwd(), 'data', 'mock-users.json')

class FileUserStore {
  private users: MockUser[] = []
  private nextId = 1
  private loaded = false

  private async ensureLoaded() {
    if (this.loaded) return
    await fs.mkdir(path.dirname(DATA_PATH), { recursive: true })

    try {
      const raw = await fs.readFile(DATA_PATH, 'utf-8')
      const parsed: PersistedUser[] = JSON.parse(raw)
      this.users = parsed.map((u) => ({
        ...u,
        createdAt: new Date(u.createdAt),
      }))
      this.nextId = this.users.reduce((max, u) => Math.max(max, u.id), 0) + 1
    } catch (error) {
      await this.bootstrap()
    }

    this.loaded = true
  }

  private async bootstrap() {
    // Seed a demo user for local logins (NOT FOR PRODUCTION - mock data only)
    const seedPassword = await bcrypt.hash('<DEMO_PASSWORD>', 12)
    this.users = [
      {
        id: 1,
        username: 'demo',
        password: seedPassword,
        email: 'demo@example.com',
        firstName: 'Demo',
        lastName: 'User',
        role: 'patient',
        profilePicture: null,
        phone: null,
        preferredContactMethod: null,
        createdAt: new Date(),
      },
    ]
    this.nextId = 2
    await this.persist()
  }

  private async persist() {
    const serialized: PersistedUser[] = this.users.map((u) => ({
      ...u,
      createdAt: u.createdAt.toISOString(),
    }))
    await fs.writeFile(DATA_PATH, JSON.stringify(serialized, null, 2), 'utf-8')
  }

  async getUserByUsername(username: string) {
    await this.ensureLoaded()
    return this.users.find((u) => u.username === username) ?? null
  }

  async getUserByEmail(email: string) {
    await this.ensureLoaded()
    return this.users.find((u) => u.email === email) ?? null
  }

  async createUser(data: Omit<MockUser, 'id' | 'createdAt'>) {
    await this.ensureLoaded()
    const user: MockUser = {
      ...data,
      id: this.nextId++,
      createdAt: new Date(),
    }
    this.users.push(user)
    await this.persist()
    return user
  }
}

export const mockStore = new FileUserStore()
