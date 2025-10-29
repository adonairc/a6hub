'use client';

import Link from 'next/link';
import { Cpu, Code, Zap, Users, ChevronRight, Github } from 'lucide-react';

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-black">
        <nav className="container bg-white  mx-auto px-4 py-4 flex items-center justify-between fixed">
          <Link href="/" className="text-2xl font-bold tracking-tight">
            a6hub
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/auth/login" className="px-4 py-2 hover:bg-gray-100 transition-colors">
              Sign In
            </Link>
            <Link href="/auth/register" className="btn-primary">
              Get Started
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20 md:py-32">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl md:text-7xl font-bold mb-6 tracking-tight">
            Design Chips
            <br />
            <span className="text-gray-600">In Your Browser</span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 mb-8 leading-relaxed">
            Cloud-based platform for collaborative ASIC design.
            <br />
            From RTL to GDSII, all in one place.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/auth/register" className="btn-primary text-lg px-8 py-4 inline-flex items-center justify-center gap-2">
              Start Designing
              <ChevronRight className="w-5 h-5" />
            </Link>
            <Link href="#features" className="btn-secondary text-lg px-8 py-4 inline-flex items-center justify-center">
              Learn More
            </Link>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-black text-white py-20 md:py-32">
        <div className="container mx-auto px-4">
          <h2 className="text-4xl md:text-5xl font-bold text-center mb-16">
            Everything You Need
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            <FeatureCard
              icon={<Code className="w-8 h-8" />}
              title="HDL Editor"
              description="Write Verilog and SystemVerilog with syntax highlighting and auto-completion."
            />
            <FeatureCard
              icon={<Zap className="w-8 h-8" />}
              title="Fast Simulation"
              description="Run simulations with Verilator and Icarus Verilog in the cloud."
            />
            <FeatureCard
              icon={<Cpu className="w-8 h-8" />}
              title="RTL to GDSII"
              description="Complete ASIC flow with LibreLane and open-source PDKs."
            />
            <FeatureCard
              icon={<Users className="w-8 h-8" />}
              title="Collaborate"
              description="Share projects, fork designs, and build together."
            />
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="container mx-auto px-4 py-20 md:py-32">
        <h2 className="text-4xl md:text-5xl font-bold text-center mb-16">
          How It Works
        </h2>
        <div className="max-w-4xl mx-auto space-y-12">
          <Step
            number="01"
            title="Create a Project"
            description="Start with a template or from scratch. Organize your HDL files, testbenches, and configurations."
          />
          <Step
            number="02"
            title="Write & Simulate"
            description="Use our in-browser editor to write Verilog. Run simulations and view waveforms instantly."
          />
          <Step
            number="03"
            title="Build & Deploy"
            description="Execute the full RTL-to-GDSII flow. Download your GDSII files ready for fabrication."
          />
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-black text-white py-20 md:py-32">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Ready to Build?
          </h2>
          <p className="text-xl text-gray-300 mb-8">
            Join the community of chip designers building the future.
          </p>
          <Link href="/auth/register" className="bg-white text-black px-8 py-4 text-lg font-medium hover:bg-gray-100 transition-colors inline-flex items-center gap-2">
            Get Started Free
            <ChevronRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-2xl font-bold">a6hub</div>
            <div className="flex items-center gap-6">
              <Link href="#" className="text-gray-600 hover:text-black transition-colors">
                Docs
              </Link>
              <Link href="#" className="text-gray-600 hover:text-black transition-colors">
                Blog
              </Link>
              <Link href="#" className="text-gray-600 hover:text-black transition-colors inline-flex items-center gap-2">
                <Github className="w-5 h-5" />
                GitHub
              </Link>
            </div>
          </div>
          <div className="text-center mt-8 text-gray-500">
            © 2025 a6hub. Open-source chip design for everyone.
          </div>
        </div>
      </footer>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="border border-white p-8">
      <div className="mb-4">{icon}</div>
      <h3 className="text-xl font-bold mb-2">{title}</h3>
      <p className="text-gray-300">{description}</p>
    </div>
  );
}

function Step({ number, title, description }: { number: string; title: string; description: string }) {
  return (
    <div className="flex gap-8 items-start">
      <div className="text-6xl font-bold text-gray-200 flex-shrink-0">{number}</div>
      <div>
        <h3 className="text-2xl font-bold mb-3">{title}</h3>
        <p className="text-gray-600 text-lg">{description}</p>
      </div>
    </div>
  );
}
