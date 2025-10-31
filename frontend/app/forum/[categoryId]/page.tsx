'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { forumAPI } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { MessageSquare, Eye, Pin, Lock, Plus, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';

interface Topic {
  id: number;
  title: string;
  slug: string;
  author_username: string;
  is_pinned: boolean;
  is_locked: boolean;
  views_count: number;
  post_count: number;
  created_at: string;
  last_post_at: string;
}

export default function CategoryPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const categoryId = parseInt(params.categoryId as string);

  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewTopicModal, setShowNewTopicModal] = useState(false);

  useEffect(() => {
    loadTopics();
  }, [categoryId]);

  const loadTopics = async () => {
    try {
      const response = await forumAPI.listTopics(categoryId, { limit: 50 });
      setTopics(response.data);
    } catch (error) {
      toast.error('Failed to load topics');
    } finally {
      setLoading(false);
    }
  };

  const handleNewTopic = () => {
    if (!user) {
      toast.error('Please sign in to create a topic');
      router.push('/auth/login');
      return;
    }
    setShowNewTopicModal(true);
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200">
        <div className="container mx-auto px-8 py-6">
          <Link href="/forum" className="inline-flex items-center gap-2 text-gray-600 hover:text-black mb-3">
            <ArrowLeft className="w-4 h-4" />
            Back to forum
          </Link>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold">Topics</h1>
            </div>
            <button
              onClick={handleNewTopic}
              className="btn-primary flex items-center gap-2"
            >
              <Plus className="w-4 h-4" />
              New Topic
            </button>
          </div>
        </div>
      </header>

      {/* Topics List */}
      <div className="container mx-auto px-8 py-12">
        {loading ? (
          <div className="text-center py-12">
            <div className="text-gray-500">Loading topics...</div>
          </div>
        ) : topics.length === 0 ? (
          <div className="text-center py-12">
            <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-300" />
            <h3 className="text-xl font-semibold mb-2">No topics yet</h3>
            <p className="text-gray-600 mb-6">Be the first to start a discussion</p>
            <button onClick={handleNewTopic} className="btn-primary">
              Create First Topic
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {topics.map((topic) => (
              <Link
                key={topic.id}
                href={`/forum/topic/${topic.id}`}
                className="block border border-gray-200 hover:border-black p-4 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {topic.is_pinned && (
                        <Pin className="w-4 h-4 text-blue-600 flex-shrink-0" />
                      )}
                      {topic.is_locked && (
                        <Lock className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      )}
                      <h3 className="text-lg font-semibold truncate">{topic.title}</h3>
                    </div>
                    <p className="text-sm text-gray-600">
                      by <span className="font-medium">{topic.author_username}</span>
                      {' • '}
                      {new Date(topic.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-6 text-sm text-gray-500 flex-shrink-0">
                    <div className="flex items-center gap-1">
                      <MessageSquare className="w-4 h-4" />
                      <span>{topic.post_count}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Eye className="w-4 h-4" />
                      <span>{topic.views_count}</span>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* New Topic Modal */}
      {showNewTopicModal && (
        <NewTopicModal
          categoryId={categoryId}
          onClose={() => setShowNewTopicModal(false)}
          onSuccess={() => {
            setShowNewTopicModal(false);
            loadTopics();
          }}
        />
      )}
    </div>
  );
}

function NewTopicModal({
  categoryId,
  onClose,
  onSuccess,
}: {
  categoryId: number;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [content, setContent] = useState('');
  const [creating, setCreating] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!title.trim() || !content.trim()) {
      toast.error('Please fill in all fields');
      return;
    }

    setCreating(true);
    try {
      const response = await forumAPI.createTopic({
        title: title.trim(),
        category_id: categoryId,
        content: content.trim(),
      });
      toast.success('Topic created successfully!');
      router.push(`/forum/topic/${response.data.id}`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to create topic');
    } finally {
      setCreating(false);
    }
  };

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white w-full max-w-2xl border-2 border-black"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="border-b border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold">Create New Topic</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-black text-2xl font-bold leading-none"
            >
              ×
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <label htmlFor="title" className="block text-sm font-medium mb-2">
              Title *
            </label>
            <input
              id="title"
              type="text"
              required
              className="input"
              placeholder="What's your topic about?"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={200}
            />
          </div>

          <div>
            <label htmlFor="content" className="block text-sm font-medium mb-2">
              Content *
            </label>
            <textarea
              id="content"
              required
              rows={8}
              className="input resize-none"
              placeholder="Provide more details..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
            />
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              disabled={creating}
              className="btn-primary px-8 disabled:opacity-50"
            >
              {creating ? 'Creating...' : 'Create Topic'}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary px-8"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
