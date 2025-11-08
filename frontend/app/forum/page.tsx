'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { forumAPI } from '@/lib/api';
import { MessageSquare, Users, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';

interface Category {
  id: number;
  name: string;
  description: string | null;
  slug: string;
  order: number;
  icon: string | null;
  topic_count: number;
  post_count: number;
  created_at: string;
}

export default function ForumPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const response = await forumAPI.listCategories();
      setCategories(response.data);
    } catch (error) {
      toast.error('Failed to load categories');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200">
        <div className="container mx-auto px-8 py-6">
          <Link href="/" className="inline-flex items-center gap-2 text-gray-600 hover:text-black mb-3">
            <ArrowLeft className="w-4 h-4" />
            Back to home
          </Link>
          <h1 className="text-4xl font-bold">Community Forum</h1>
          <p className="text-gray-600 mt-2">Discuss chip design, share knowledge, and get help from the community</p>
        </div>
      </header>

      {/* Categories */}
      <div className="container mx-auto px-8 py-12">
        {loading ? (
          <div className="text-center py-12">
            <div className="text-gray-500">Loading categories...</div>
          </div>
        ) : categories.length === 0 ? (
          <div className="text-center py-12">
            <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-xl font-semibold mb-2">No categories yet</h3>
            <p className="text-gray-600">Forum categories will appear here</p>
          </div>
        ) : (
          <div className="space-y-4">
            {categories.map((category) => (
              <Link
                key={category.id}
                href={`/forum/${category.id}`}
                className="block border-2 border-gray-200 hover:border-black p-6 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h2 className="text-2xl font-bold mb-2">{category.name}</h2>
                    {category.description && (
                      <p className="text-gray-600 mb-4">{category.description}</p>
                    )}
                    <div className="flex items-center gap-6 text-sm text-gray-500">
                      <div className="flex items-center gap-2">
                        <MessageSquare className="w-4 h-4" />
                        <span>{category.topic_count} {category.topic_count === 1 ? 'topic' : 'topics'}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Users className="w-4 h-4" />
                        <span>{category.post_count} {category.post_count === 1 ? 'post' : 'posts'}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
