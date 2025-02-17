from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ✅ 사용자 모델
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

# ✅ 게시물 모델
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    views = db.Column(db.Integer, default=0)
    upvotes = db.Column(db.Integer, default=0)  # 추천
    downvotes = db.Column(db.Integer, default=0)  # 비추천
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))  # SQLAlchemy 2.0 버전에 맞춰 수정

# ✅ 홈페이지
@app.route('/')
def home():
    return redirect(url_for('posts', category='공지사항'))

# ✅ 게시글 목록 (카테고리별)
@app.route('/posts/<category>')
def posts(category):
    posts = Post.query.filter_by(category=category).all()
    return render_template('posts.html', posts=posts, category=category)

# ✅ 게시글 작성
@app.route('/create/<category>', methods=['GET', 'POST'])
@login_required
def create(category):
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_post = Post(title=title, content=content, author=current_user.username, category=category)
        db.session.add(new_post)
        db.session.commit()
        flash('게시글이 작성되었습니다.')
        return redirect(url_for('posts', category=category))

    return render_template('create.html', category=category)

# ✅ 게시글 수정
@app.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user.username:
        flash('수정 권한이 없습니다.')
        return redirect(url_for('post_detail', post_id=post.id))

    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        return redirect(url_for('post_detail', post_id=post.id))

    return render_template('edit_post.html', post=post)

# ✅ 게시글 삭제
@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user.username:
        flash('삭제 권한이 없습니다.')
        return redirect(url_for('post_detail', post_id=post.id))

    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('posts', category=post.category))

# ✅ 추천 기능
@app.route('/post/<int:post_id>/upvote', methods=['POST'])
@login_required
def upvote(post_id):
    post = Post.query.get_or_404(post_id)
    post.upvotes += 1
    db.session.commit()
    return redirect(url_for('post_detail', post_id=post.id))

# ✅ 비추천 기능
@app.route('/post/<int:post_id>/downvote', methods=['POST'])
@login_required
def downvote(post_id):
    post = Post.query.get_or_404(post_id)
    post.downvotes += 1
    db.session.commit()
    return redirect(url_for('post_detail', post_id=post.id))

# ✅ 조회수 기능
@app.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    
    # 조회수 증가
    post.views += 1
    db.session.commit()

    return render_template('post_detail.html', post=post)

# ✅ 로그인
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash('로그인 실패! 아이디 또는 비밀번호를 확인하세요.')
    return render_template('login.html')

# ✅ 로그아웃
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# ✅ 회원가입
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash('회원가입이 완료되었습니다.')
        return redirect(url_for('login'))
    return render_template('register.html')

# ✅ DB 초기화
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
