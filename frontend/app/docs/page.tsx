'use client';

import Link from 'next/link';
import { ArrowLeft, FileText, Zap, Cpu, Code, Settings as SettingsIcon } from 'lucide-react';

export default function DocsPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200">
        <div className="container mx-auto px-8 py-6">
          <Link href="/" className="inline-flex items-center gap-2 text-gray-600 hover:text-black mb-3">
            <ArrowLeft className="w-4 h-4" />
            Back to home
          </Link>
          <h1 className="text-4xl font-bold">Documentation</h1>
          <p className="text-gray-600 mt-2">Learn how to use a6hub for your chip design projects</p>
        </div>
      </header>

      <div className="container mx-auto px-8 py-12">
        <div className="grid lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <aside className="lg:col-span-1">
            <nav className="space-y-1 sticky top-8">
              <a href="#getting-started" className="block px-4 py-2 text-sm hover:bg-gray-100 rounded">
                Getting Started
              </a>
              <a href="#design" className="block px-4 py-2 text-sm hover:bg-gray-100 rounded">
                Design Editor
              </a>
              <a href="#simulation" className="block px-4 py-2 text-sm hover:bg-gray-100 rounded">
                Simulation
              </a>
              <a href="#build" className="block px-4 py-2 text-sm hover:bg-gray-100 rounded">
                Build & Synthesis
              </a>
              <a href="#collaboration" className="block px-4 py-2 text-sm hover:bg-gray-100 rounded">
                Collaboration
              </a>
            </nav>
          </aside>

          {/* Main content */}
          <main className="lg:col-span-3 prose max-w-none">
            <section id="getting-started" className="mb-16">
              <h2 className="text-3xl font-bold mb-6 flex items-center gap-3">
                <FileText className="w-8 h-8" />
                Getting Started
              </h2>

              <div className="bg-gray-50 border border-gray-200 p-6 rounded mb-6">
                <h3 className="text-xl font-semibold mb-3">Welcome to a6hub</h3>
                <p className="text-gray-700 mb-4">
                  a6hub is a cloud-based platform for collaborative ASIC design. Design, simulate, and synthesize
                  your chip designs entirely in your browser using industry-standard open-source tools.
                </p>
              </div>

              <h3 className="text-2xl font-semibold mb-4">Quick Start</h3>
              <ol className="space-y-4 list-decimal list-inside">
                <li className="text-gray-800">
                  <strong>Create an account</strong> - Sign up for free at{' '}
                  <Link href="/auth/register" className="text-blue-600 hover:underline">
                    /auth/register
                  </Link>
                </li>
                <li className="text-gray-800">
                  <strong>Create a project</strong> - Click "New Project" from your dashboard
                </li>
                <li className="text-gray-800">
                  <strong>Add your design files</strong> - Upload or create Verilog/SystemVerilog files
                </li>
                <li className="text-gray-800">
                  <strong>Run simulations</strong> - Test your design with Verilator or Icarus Verilog
                </li>
                <li className="text-gray-800">
                  <strong>Synthesize</strong> - Use LibreLane to generate GDSII files for fabrication
                </li>
              </ol>
            </section>

            <section id="design" className="mb-16">
              <h2 className="text-3xl font-bold mb-6 flex items-center gap-3">
                <Code className="w-8 h-8" />
                Design Editor
              </h2>

              <h3 className="text-2xl font-semibold mb-4">Creating Files</h3>
              <p className="mb-4">
                The Design tab provides a code editor for your HDL files. You can:
              </p>
              <ul className="list-disc list-inside space-y-2 mb-6">
                <li>Create new Verilog (.v) or SystemVerilog (.sv) files</li>
                <li>Organize files in the Modules and Macros sections</li>
                <li>Use syntax highlighting optimized for hardware design</li>
                <li>Auto-save your changes</li>
              </ul>

              <div className="bg-blue-50 border border-blue-200 p-4 rounded mb-6">
                <p className="text-sm text-blue-900">
                  <strong>Tip:</strong> Use the Save button in the top-right corner to save your changes.
                  The editor will show line counts and file paths for easy navigation.
                </p>
              </div>

              <h3 className="text-2xl font-semibold mb-4">Supported Languages</h3>
              <ul className="list-disc list-inside space-y-2">
                <li>Verilog (IEEE 1364-2005)</li>
                <li>SystemVerilog (IEEE 1800-2017)</li>
                <li>VHDL (coming soon)</li>
              </ul>
            </section>

            <section id="simulation" className="mb-16">
              <h2 className="text-3xl font-bold mb-6 flex items-center gap-3">
                <Zap className="w-8 h-8" />
                Simulation
              </h2>

              <h3 className="text-2xl font-semibold mb-4">Running Simulations</h3>
              <p className="mb-4">
                The Simulation tab allows you to test your design with industry-standard simulators:
              </p>

              <div className="space-y-4 mb-6">
                <div className="border border-gray-200 p-4 rounded">
                  <h4 className="font-semibold mb-2">Verilator</h4>
                  <p className="text-sm text-gray-700">
                    Fast, cycle-accurate simulator perfect for large designs. Best for performance testing
                    and regression suites.
                  </p>
                </div>
                <div className="border border-gray-200 p-4 rounded">
                  <h4 className="font-semibold mb-2">Icarus Verilog</h4>
                  <p className="text-sm text-gray-700">
                    Event-driven simulator with full Verilog support. Ideal for functional verification
                    and waveform generation.
                  </p>
                </div>
              </div>

              <h3 className="text-2xl font-semibold mb-4">Configuration</h3>
              <ul className="list-disc list-inside space-y-2">
                <li>Select your simulator (Verilator or Icarus)</li>
                <li>Specify testbench file</li>
                <li>Configure timescale (e.g., 1ns/1ps)</li>
                <li>Enable waveform dumping for debugging</li>
              </ul>
            </section>

            <section id="build" className="mb-16">
              <h2 className="text-3xl font-bold mb-6 flex items-center gap-3">
                <Cpu className="w-8 h-8" />
                Build & Synthesis
              </h2>

              <h3 className="text-2xl font-semibold mb-4">LibreLane Integration</h3>
              <p className="mb-4">
                a6hub uses{' '}
                <a href="https://github.com/librelane/librelane" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
                  LibreLane
                </a>
                {' '}to provide a complete RTL-to-GDSII flow using open-source tools:
              </p>

              <ul className="list-disc list-inside space-y-2 mb-6">
                <li><strong>Synthesis:</strong> Yosys converts RTL to gate-level netlist</li>
                <li><strong>Place & Route:</strong> OpenROAD handles physical design</li>
                <li><strong>Verification:</strong> Magic for DRC and Netgen for LVS</li>
                <li><strong>Output:</strong> GDSII files ready for fabrication</li>
              </ul>

              <h3 className="text-2xl font-semibold mb-4">Quick Start Presets</h3>
              <div className="grid md:grid-cols-3 gap-4 mb-6">
                <div className="border border-gray-200 p-4 rounded">
                  <h4 className="font-semibold mb-2">Minimal</h4>
                  <p className="text-sm text-gray-700">Fast builds for quick iterations</p>
                </div>
                <div className="border border-gray-200 p-4 rounded">
                  <h4 className="font-semibold mb-2">Balanced</h4>
                  <p className="text-sm text-gray-700">Good quality with reasonable runtime</p>
                </div>
                <div className="border border-gray-200 p-4 rounded">
                  <h4 className="font-semibold mb-2">High Quality</h4>
                  <p className="text-sm text-gray-700">Production-ready builds</p>
                </div>
              </div>

              <h3 className="text-2xl font-semibold mb-4">Supported PDKs</h3>
              <ul className="list-disc list-inside space-y-2">
                <li>SkyWater 130nm (sky130_fd_sc_hd, hs, ms, ls)</li>
                <li>GlobalFoundries 180nm (gf180mcuC)</li>
              </ul>
            </section>

            <section id="collaboration" className="mb-16">
              <h2 className="text-3xl font-bold mb-6 flex items-center gap-3">
                <SettingsIcon className="w-8 h-8" />
                Collaboration
              </h2>

              <h3 className="text-2xl font-semibold mb-4">Project Visibility</h3>
              <p className="mb-4">
                Control who can see your projects:
              </p>
              <ul className="list-disc list-inside space-y-2 mb-6">
                <li><strong>Private:</strong> Only you can access the project</li>
                <li><strong>Public:</strong> Anyone can view (but not edit) your project</li>
              </ul>

              <h3 className="text-2xl font-semibold mb-4">Sharing Projects</h3>
              <p className="mb-4">
                Public projects appear on the homepage and can be viewed by anyone. This is great for:
              </p>
              <ul className="list-disc list-inside space-y-2">
                <li>Showcasing your designs</li>
                <li>Educational content</li>
                <li>Open-source hardware projects</li>
                <li>Portfolio pieces</li>
              </ul>
            </section>

            <section id="support" className="mb-16">
              <h2 className="text-3xl font-bold mb-6">Need Help?</h2>
              <div className="bg-gray-50 border border-gray-200 p-6 rounded">
                <p className="mb-4">
                  If you have questions or need assistance:
                </p>
                <ul className="space-y-3">
                  <li>
                    <strong>GitHub Issues:</strong>{' '}
                    <a href="https://github.com/adonairc/a6hub" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
                      Report bugs or request features
                    </a>
                  </li>
                  <li>
                    <strong>LibreLane Docs:</strong>{' '}
                    <a href="https://github.com/librelane/librelane" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
                      Learn more about the synthesis flow
                    </a>
                  </li>
                </ul>
              </div>
            </section>
          </main>
        </div>
      </div>
    </div>
  );
}
