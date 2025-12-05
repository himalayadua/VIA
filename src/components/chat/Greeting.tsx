/**
 * Greeting Component
 * 
 * Displays a welcoming greeting message when chat is empty.
 */

export const Greeting = () => {
  return (
    <div className="text-center py-8 animate-fade-in">
      <h2 className="text-2xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
        Via Canvas Assistant
      </h2>
      <p className="text-sm text-slate-400 mt-2">
        Your AI-powered canvas companion
      </p>
    </div>
  );
};
