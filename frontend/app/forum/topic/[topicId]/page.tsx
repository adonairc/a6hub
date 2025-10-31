'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { forumAPI } from '@/lib/api';
import { useAuth } from '@/lib/auth-context';
import { ArrowLeft, MessageSquare, Eye, Pin, Lock } from 'lucide-react';
import toast from 'react-hot-toast';

interface Topic {
  id: number;
  title: string;
  category_id: number;
  category_name: string;
  author_username: string;
  is_pinned: boolean;
  is_locked: boolean;
  views_count: number;
  created_at: string;
}

interface Post {
  id: number;
  content: string;
  author_id: number;
  author_username: string;
  is_edited: boolean;
  edited_at: string | null;
  created_at: string;
}

export default function TopicPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const topicId = parseInt(params.topicId as string);

  const [topic, setTopic] = useState<Topic | null>(null);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [replyContent, setReplyContent] = useState('');
  const [replying, setReplying] = useState(false);

  useEffect(() => {
    loadTopic();
    loadPosts();
  }, [topicId]);

  const loadTopic = async () => {
    try {
      const response = await forumAPI.getTopic(topicId);
      setTopic(response.data);
    } catch (error) {
      toast.error('Failed to load topic');
    }
  };

  const loadPosts = async () => {
    try {
      const response = await forumAPI.listPosts(topicId, { limit: 100 });
      setPosts(response.data);
    } catch (error) {
      toast.error('Failed to load posts');
    } finally {
      setLoading(false);
    }
  };

  const handleReply = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!user) {
      toast.error('Please sign in to reply');
      router.push('/auth/login');
      return;
    }

    if (!replyContent.trim()) {
      toast.error('Please enter a message');
      return;
    }

    setReplying(true);
    try {
      await forumAPI.createPost(topicId, { content: replyContent.trim() });
      toast.success('Reply posted!');
      setReplyContent('');
      loadPosts();
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to post reply');
    } finally {
      setReplying(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!topic) {
    return null;
  }

  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200">
        <div className="container mx-auto px-8 py-6">
          <Link
            href={`/forum/${topic.category_id}`}
            className="inline-flex items-center gap-2 text-gray-600 hover:text-black mb-3"
          >
            <ArrowLeft className="w-4 h-4" />
            Back to {topic.category_name}
          </Link>
          <div className="flex items-start gap-3 mb-2">
            {topic.is_pinned && <Pin className="w-5 h-5 text-blue-600 mt-1" />}
            {topic.is_locked && <Lock className="w-5 h-5 text-gray-400 mt-1" />}
            <h1 className="text-4xl font-bold">{topic.title}</h1>
          </div>
          <div className="flex items-center gap-6 text-sm text-gray-600">
            <span>by <span className="font-medium">{topic.author_username}</span></span>
            <div className="flex items-center gap-1">
              <Eye className="w-4 h-4" />
              <span>{topic.views_count} views</span>
            </div>
            <div className="flex items-center gap-1">
              <MessageSquare className="w-4 h-4" />
              <span>{posts.length} posts</span>
            </div>
          </div>
        </div>
      </header>

      {/* Posts */}
      <div className="container mx-auto px-8 py-12 max-w-4xl">
        <div className="space-y-6">
          {posts.map((post, index) => (
            <div
              key={post.id}
              className="border-2 border-gray-200 p-6"
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 rounded-full bg-black text-white flex items-center justify-center font-bold">
                    {post.author_username.charAt(0).toUpperCase()}
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold">{post.author_username}</span>
                    <span className="text-sm text-gray-500">
                      {new Date(post.created_at).toLocaleString()}
                    </span>
                    {index === 0 && (
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        Original Post
                      </span>
                    )}
                    {post.is_edited && (
                      <span className="text-xs text-gray-500">(edited)</span>
                    )}
                  </div>
                  <div className="prose max-w-none">
                    <p className="whitespace-pre-wrap">{post.content}</p>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Reply Form */}
        {topic.is_locked ? (
          <div className="mt-8 border-2 border-gray-200 p-6 text-center">
            <Lock className="w-8 h-8 mx-auto mb-2 text-gray-400" />
            <p className="text-gray-600">This topic is locked and cannot receive new replies</p>
          </div>
        ) : user ? (
          <form onSubmit={handleReply} className="mt-8 border-2 border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Post a Reply</h3>
            <textarea
              rows={6}
              className="input resize-none mb-4"
              placeholder="Write your reply..."
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
              disabled={replying}
            />
            <button
              type="submit"
              disabled={replying || !replyContent.trim()}
              className="btn-primary disabled:opacity-50"
            >
              {replying ? 'Posting...' : 'Post Reply'}
            </button>
          </form>
        ) : (
          <div className="mt-8 border-2 border-gray-200 p-6 text-center">
            <p className="text-gray-600 mb-4">Sign in to post a reply</p>
            <Link href="/auth/login" className="btn-primary inline-block">
              Sign In
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
