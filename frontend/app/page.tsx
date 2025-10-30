'use client';

import Link from 'next/link';
import { Cpu, Code, Zap, Users, ChevronRight, Github, Star, Eye } from 'lucide-react';
import { useEffect, useState } from 'react';
import { projectsAPI } from '@/lib/api';

interface Project {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  visibility: string;
  owner_id: number;
  stars_count: number;
  views_count: number;
  created_at: string;
}

export default function Home() {
  const [publicProjects, setPublicProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPublicProjects();
  }, []);

  const loadPublicProjects = async () => {
    try {
      const response = await projectsAPI.listPublic({ limit: 6 });
      setPublicProjects(response.data);
    } catch (error) {
      console.error('Failed to load public projects:', error);
    } finally {
      setLoading(false);
    }
  };

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

            {/* Public Projects Section */}
      <section className="bg-gray-50 py-20 md:py-32">
        <div className="container mx-auto px-4">
        <h2 className="text-4xl md:text-5xl font-bold text-center mb-4">
          Explore Projects
        </h2>
        <p className="text-center text-gray-600 text-lg mb-12">
          Discover popular chip designs from the community
        </p>

        {loading ? (
          <div className="flex justify-center items-center py-20">
            <div className="text-gray-500">Loading projects...</div>
          </div>
        ) : publicProjects.length === 0 ? (
          <div className="text-center text-gray-500 py-20">
            No public projects yet. Be the first to share your design!
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {publicProjects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onClick={() => setSelectedProject(project)}
              />
            ))}
          </div>
        )}
        </div>
      </section>

      {/* Project Details Modal */}
      {selectedProject && (
        <ProjectModal
          project={selectedProject}
          onClose={() => setSelectedProject(null)}
        />
      )}

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

function ProjectCard({ project, onClick }: { project: Project; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="bg-white border-2 border-black p-6 hover:bg-gray-50 transition-colors text-left w-full"
    >
      <h3 className="text-xl font-bold mb-2">{project.name}</h3>
      <p className="text-gray-600 mb-4 line-clamp-2 min-h-[3rem]">
        {project.description || 'No description'}
      </p>
      <div className="flex items-center gap-4 text-sm text-gray-500">
        <div className="flex items-center gap-1">
          <Star className="w-4 h-4" />
          <span>{project.stars_count}</span>
        </div>
        <div className="flex items-center gap-1">
          <Eye className="w-4 h-4" />
          <span>{project.views_count}</span>
        </div>
        <div className="ml-auto text-xs">
          {new Date(project.created_at).toLocaleDateString()}
        </div>
      </div>
    </button>
  );
}

function ProjectModal({ project, onClose }: { project: Project; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white border-2 border-black p-8 max-w-2xl w-full max-h-[80vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-start mb-6">
          <h2 className="text-3xl font-bold">{project.name}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-black text-2xl font-bold"
          >
            ×
          </button>
        </div>

        <div className="space-y-6">
          <div>
            <h3 className="text-sm font-semibold text-gray-500 mb-2">DESCRIPTION</h3>
            <p className="text-gray-700">
              {project.description || 'No description provided'}
            </p>
          </div>

          <div className="flex items-center gap-6">
            <div>
              <h3 className="text-sm font-semibold text-gray-500 mb-1">POPULARITY</h3>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-1">
                  <Star className="w-5 h-5" />
                  <span className="font-semibold">{project.stars_count}</span>
                  <span className="text-gray-500 text-sm">stars</span>
                </div>
                <div className="flex items-center gap-1">
                  <Eye className="w-5 h-5" />
                  <span className="font-semibold">{project.views_count}</span>
                  <span className="text-gray-500 text-sm">views</span>
                </div>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-500 mb-1">PROJECT ID</h3>
            <p className="text-gray-700">{project.slug}</p>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-500 mb-1">CREATED</h3>
            <p className="text-gray-700">
              {new Date(project.created_at).toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })}
            </p>
          </div>

          <div className="pt-4 border-t border-gray-200">
            <p className="text-center text-gray-600 mb-4">
              Sign in to view, fork, or collaborate on this project
            </p>
            <div className="flex gap-3">
              <Link
                href="/auth/login"
                className="btn-secondary flex-1 text-center"
                onClick={onClose}
              >
                Sign In
              </Link>
              <Link
                href="/auth/register"
                className="btn-primary flex-1 text-center"
                onClick={onClose}
              >
                Create Account
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
