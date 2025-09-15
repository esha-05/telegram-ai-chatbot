import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';
import { useDropzone } from 'react-dropzone';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { ScrollArea } from './components/ui/scroll-area';
import { Separator } from './components/ui/separator';
import { toast } from 'sonner';
import { Toaster } from './components/ui/sonner';
import { 
  User, 
  MessageCircle, 
  Upload, 
  Search, 
  Send, 
  Bot, 
  FileText,
  Image,
  History,
  Clock
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [chatHistory, setChatHistory] = useState([]);
  const [message, setMessage] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [userFiles, setUserFiles] = useState([]);
  const [searchHistory, setSearchHistory] = useState([]);
  const chatEndRef = useRef(null);

  // Registration form state
  const [registrationData, setRegistrationData] = useState({
    first_name: '',
    username: '',
    phone: ''
  });

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const handleRegistration = async (e) => {
    e.preventDefault();
    if (!registrationData.first_name) {
      toast.error('First name is required');
      return;
    }

    try {
      setIsLoading(true);
      const response = await axios.post(`${API}/users`, registrationData);
      setCurrentUser(response.data);
      toast.success('Registration successful!');
      
      // Load user data
      await loadUserData(response.data.id);
    } catch (error) {
      console.error('Registration error:', error);
      toast.error('Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const loadUserData = async (userId) => {
    try {
      // Load chat history
      const chatResponse = await axios.get(`${API}/chat/${userId}`);
      setChatHistory(chatResponse.data);

      // Load user files
      const filesResponse = await axios.get(`${API}/files/${userId}`);
      setUserFiles(filesResponse.data);

      // Load search history
      const searchResponse = await axios.get(`${API}/search/${userId}`);
      setSearchHistory(searchResponse.data);
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  const handleChat = async (e) => {
    e.preventDefault();
    if (!message.trim() || !currentUser) return;

    try {
      setIsLoading(true);
      const response = await axios.post(`${API}/chat`, {
        user_id: currentUser.id,
        message: message
      });

      setChatHistory(prev => [...prev, response.data]);
      setMessage('');
      toast.success('Message sent!');
    } catch (error) {
      console.error('Chat error:', error);
      toast.error('Failed to send message. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileUpload = async (acceptedFiles) => {
    if (!currentUser) {
      toast.error('Please register first');
      return;
    }

    const file = acceptedFiles[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('user_id', currentUser.id);

    try {
      setIsLoading(true);
      const response = await axios.post(`${API}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUserFiles(prev => [response.data, ...prev]);
      toast.success('File uploaded and analyzed successfully!');
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to upload file. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleWebSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim() || !currentUser) return;

    try {
      setIsLoading(true);
      const response = await axios.post(`${API}/websearch`, {
        user_id: currentUser.id,
        query: searchQuery
      });

      setSearchHistory(prev => [response.data, ...prev]);
      setSearchQuery('');
      toast.success('Search completed!');
    } catch (error) {
      console.error('Search error:', error);
      toast.error('Search failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleFileUpload,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'application/pdf': ['.pdf']
    },
    multiple: false
  });

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString();
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-xl">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl font-bold text-gray-800">Welcome to AI Assistant</CardTitle>
            <CardDescription>Register to get started with your personal AI chatbot</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleRegistration} className="space-y-4">
              <div>
                <Input
                  placeholder="First Name *"
                  value={registrationData.first_name}
                  onChange={(e) => setRegistrationData(prev => ({
                    ...prev,
                    first_name: e.target.value
                  }))}
                  required
                />
              </div>
              <div>
                <Input
                  placeholder="Username (optional)"
                  value={registrationData.username}
                  onChange={(e) => setRegistrationData(prev => ({
                    ...prev,
                    username: e.target.value
                  }))}
                />
              </div>
              <div>
                <Input
                  placeholder="Phone Number (optional)"
                  value={registrationData.phone}
                  onChange={(e) => setRegistrationData(prev => ({
                    ...prev,
                    phone: e.target.value
                  }))}
                />
              </div>
              <Button 
                type="submit" 
                className="w-full" 
                disabled={isLoading}
              >
                {isLoading ? 'Registering...' : 'Register'}
              </Button>
            </form>
          </CardContent>
        </Card>
        <Toaster />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto p-4">
        {/* Header */}
        <Card className="mb-6 shadow-lg">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-blue-500 rounded-full">
                  <Bot className="h-6 w-6 text-white" />
                </div>
                <div>
                  <CardTitle className="text-xl">AI Assistant Dashboard</CardTitle>
                  <CardDescription>Welcome back, {currentUser.first_name}!</CardDescription>
                </div>
              </div>
              <Badge variant="secondary" className="text-sm">
                <User className="h-4 w-4 mr-1" />
                {currentUser.username || 'User'}
              </Badge>
            </div>
          </CardHeader>
        </Card>

        {/* Main Content */}
        <Tabs defaultValue="chat" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 shadow-md">
            <TabsTrigger value="chat" className="flex items-center space-x-2">
              <MessageCircle className="h-4 w-4" />
              <span>Chat</span>
            </TabsTrigger>
            <TabsTrigger value="upload" className="flex items-center space-x-2">
              <Upload className="h-4 w-4" />
              <span>Upload</span>
            </TabsTrigger>
            <TabsTrigger value="search" className="flex items-center space-x-2">
              <Search className="h-4 w-4" />
              <span>Search</span>
            </TabsTrigger>
            <TabsTrigger value="history" className="flex items-center space-x-2">
              <History className="h-4 w-4" />
              <span>History</span>
            </TabsTrigger>
          </TabsList>

          {/* Chat Tab */}
          <TabsContent value="chat">
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MessageCircle className="h-5 w-5" />
                  <span>AI Chat</span>
                </CardTitle>
                <CardDescription>Chat with your AI assistant powered by GPT-5</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-96 w-full p-4 border rounded-lg bg-gray-50">
                  {chatHistory.length === 0 ? (
                    <div className="text-center text-gray-500 mt-20">
                      <Bot className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                      <p>Start a conversation with your AI assistant!</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      {chatHistory.map((chat) => (
                        <div key={chat.id}>
                          {/* User Message */}
                          <div className="flex justify-end mb-2">
                            <div className="bg-blue-500 text-white p-3 rounded-lg max-w-xs lg:max-w-md">
                              <p className="text-sm">{chat.message}</p>
                              <p className="text-xs opacity-70 mt-1">
                                {formatDate(chat.timestamp)}
                              </p>
                            </div>
                          </div>
                          {/* AI Response */}
                          <div className="flex justify-start mb-4">
                            <div className="bg-white border p-3 rounded-lg max-w-xs lg:max-w-md shadow-sm">
                              <div className="flex items-center space-x-2 mb-2">
                                <Bot className="h-4 w-4 text-blue-500" />
                                <span className="text-xs font-medium text-gray-600">AI Assistant</span>
                              </div>
                              <p className="text-sm text-gray-800">{chat.response}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                      <div ref={chatEndRef} />
                    </div>
                  )}
                </ScrollArea>
                <form onSubmit={handleChat} className="flex space-x-2 mt-4">
                  <Input
                    placeholder="Type your message..."
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    className="flex-1"
                  />
                  <Button type="submit" disabled={isLoading}>
                    <Send className="h-4 w-4" />
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Upload Tab */}
          <TabsContent value="upload">
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Upload className="h-5 w-5" />
                  <span>File Analysis</span>
                </CardTitle>
                <CardDescription>Upload JPG, PNG, or PDF files for AI analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                    isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <input {...getInputProps()} />
                  <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  {isDragActive ? (
                    <p className="text-blue-500">Drop the file here...</p>
                  ) : (
                    <div>
                      <p className="text-gray-600 mb-2">Drag & drop a file here, or click to select</p>
                      <p className="text-sm text-gray-400">Supports JPG, PNG, and PDF files</p>
                    </div>
                  )}
                </div>
                
                {userFiles.length > 0 && (
                  <div className="mt-6">
                    <h3 className="text-lg font-semibold mb-4">Your Files</h3>
                    <ScrollArea className="h-64">
                      <div className="space-y-3">
                        {userFiles.map((file) => (
                          <Card key={file.id} className="p-4">
                            <div className="flex items-start space-x-3">
                              <div className="p-2 bg-gray-100 rounded">
                                {file.file_type.startsWith('image/') ? (
                                  <Image className="h-5 w-5 text-blue-500" />
                                ) : (
                                  <FileText className="h-5 w-5 text-red-500" />
                                )}
                              </div>
                              <div className="flex-1">
                                <h4 className="font-medium text-sm">{file.filename}</h4>
                                <p className="text-xs text-gray-600 mt-1">{file.description}</p>
                                <p className="text-xs text-gray-400 mt-2 flex items-center">
                                  <Clock className="h-3 w-3 mr-1" />
                                  {formatDate(file.uploaded_at)}
                                </p>
                              </div>
                            </div>
                          </Card>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Search Tab */}
          <TabsContent value="search">
            <Card className="shadow-lg">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Search className="h-5 w-5" />
                  <span>Web Search</span>
                </CardTitle>
                <CardDescription>Search and get AI-summarized results</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleWebSearch} className="flex space-x-2 mb-6">
                  <Input
                    placeholder="Enter your search query..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="flex-1"
                  />
                  <Button type="submit" disabled={isLoading}>
                    {isLoading ? 'Searching...' : 'Search'}
                  </Button>
                </form>

                {searchHistory.length > 0 && (
                  <div>
                    <h3 className="text-lg font-semibold mb-4">Search Results</h3>
                    <ScrollArea className="h-80">
                      <div className="space-y-4">
                        {searchHistory.map((search) => (
                          <Card key={search.id} className="p-4">
                            <div className="flex items-center space-x-2 mb-2">
                              <Search className="h-4 w-4 text-blue-500" />
                              <h4 className="font-medium text-sm">{search.query}</h4>
                            </div>
                            <Separator className="my-2" />
                            <p className="text-sm text-gray-700 leading-relaxed">{search.summary}</p>
                            <p className="text-xs text-gray-400 mt-3 flex items-center">
                              <Clock className="h-3 w-3 mr-1" />
                              {formatDate(search.timestamp)}
                            </p>
                          </Card>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* History Tab */}
          <TabsContent value="history">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Chat History Summary */}
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <MessageCircle className="h-5 w-5" />
                    <span>Chat Summary</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-blue-500">{chatHistory.length}</div>
                    <p className="text-sm text-gray-600">Total Conversations</p>
                  </div>
                </CardContent>
              </Card>

              {/* Files Summary */}
              <Card className="shadow-lg">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Upload className="h-5 w-5" />
                    <span>Files Summary</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-green-500">{userFiles.length}</div>
                    <p className="text-sm text-gray-600">Files Analyzed</p>
                  </div>
                </CardContent>
              </Card>

              {/* Search Summary */}
              <Card className="shadow-lg lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <Search className="h-5 w-5" />
                    <span>Search Summary</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className="text-3xl font-bold text-purple-500">{searchHistory.length}</div>
                    <p className="text-sm text-gray-600">Searches Performed</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
      <Toaster />
    </div>
  );
}

export default App;