import os
from flask import Flask, jsonify
from models import create_app, db, Conversation

# Create Flask app using the factory function
app = create_app()

@app.route('/')
def home():
    """Home route to show bot status"""
    return jsonify({
        "status": "Jim Discord Bot is running! 🤖",
        "message": "yo what's good, Tkodv's slave is alive and ready to roast",
        "version": "2.0.0 - Unfiltered Edition"
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        # Test database connection
        with app.app_context():
            db.session.execute('SELECT 1')
        
        return jsonify({
            "status": "healthy",
            "database": "connected",
            "message": "all systems go, ready to talk shit 🔥"
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "message": "shit's broken, working on it"
        }), 500

@app.route('/stats')
def stats():
    """Get bot statistics"""
    try:
        with app.app_context():
            total_users = db.session.query(Conversation.user_id).distinct().count()
            total_conversations = Conversation.query.count()
        
        return jsonify({
            "total_users": total_users,
            "total_conversations": total_conversations,
            "message": "stats lookin good, people actually talk to me lol"
        })
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "couldn't grab stats, servers being a bitch"
        }), 500

@app.route('/ping')
def ping():
    """Simple ping endpoint"""
    return jsonify({
        "message": "pong! still alive and ready to cause chaos 🏓"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
