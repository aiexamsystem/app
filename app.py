from flask import Flask, render_template, request, redirect, url_for, session, flash,Response
import os
import random
import json
import datetime
import shutil

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于session加密

UPLOAD_FOLDER = 'static/uploads'
QUESTION_FOLDER = '题目'
IMAGE_FOLDER = '图片'
VIDEO_FOLDER = '视频'  # 新增视频文件夹
RECORDS_FILE = 'records.json'
TEACHER_PASSWORD = '123456'  # 教师登录密码

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 确保所有必要的文件夹都存在
if not os.path.exists(QUESTION_FOLDER):
    os.makedirs(QUESTION_FOLDER)
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)
if not os.path.exists(VIDEO_FOLDER):  # 新增视频文件夹创建
    os.makedirs(VIDEO_FOLDER)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_next_question_id():
    files = os.listdir(QUESTION_FOLDER)
    question_files = [f for f in files if f.startswith('question_') and f.endswith('.txt')]
    if not question_files:
        return 1
    question_ids = [int(f.split('_')[1].split('.')[0]) for f in question_files]
    return max(question_ids) + 1

def get_questions():
    files = os.listdir(QUESTION_FOLDER)
    question_files = [f for f in files if f.startswith('question_') and f.endswith('.txt')]
    questions = []
    
    for file in question_files:
        question_id = file.split('_')[1].split('.')[0]
        image_path = None
        video_path = None  # 新增视频路径变量
        
        # 检查是否有对应图片
        if f'question_{question_id}.png' in os.listdir(IMAGE_FOLDER):
            image_path = f'{IMAGE_FOLDER}/question_{question_id}.png'
        
        # 检查是否有对应视频
        video_extensions = ['.mp4', '.webm', '.ogg']
        for ext in video_extensions:
            if f'question_{question_id}{ext}' in os.listdir(VIDEO_FOLDER):
                video_path = f'{VIDEO_FOLDER}/question_{question_id}{ext}'
                break
        
        with open(os.path.join(QUESTION_FOLDER, file), 'r', encoding='utf-8') as f:
            content = f.read()
        
        questions.append({
            'id': question_id,
            'content': content,
            'image': image_path,
            'video': video_path  # 添加视频路径到问题对象
        })
    
    return questions

def save_record(student_type, questions, answers, score):
    if not os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, 'w', encoding='utf-8') as f:
            json.dump([], f)
    
    with open(RECORDS_FILE, 'r', encoding='utf-8') as f:
        records = json.load(f)
    
    record = {
        'timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'student_type': student_type,
        'questions': questions,
        'answers': answers,
        'score': score
    }
    
    records.append(record)
    
    with open(RECORDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=4)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    verification_code = request.form.get('verification_code')
    
    # 这里可以添加验证逻辑
    # 简单示例：任何用户都可登录
    if username and password and verification_code:
        session['user_logged_in'] = True
        session['username'] = username
        return redirect(url_for('role_select'))
    else:
        flash('请填写所有必填项')
        return redirect(url_for('index'))

@app.route('/register')
def register():
    # 这里可以添加注册页面，暂时重定向到登录页
    flash('注册功能待开发')
    return redirect(url_for('index'))

@app.route('/role_select')
def role_select():
    if not session.get('user_logged_in'):
        flash('请先登录')
        return redirect(url_for('index'))
    return render_template('role_select.html')

@app.route('/student')
def student():
    if not session.get('user_logged_in'):
        flash('请先登录')
        return redirect(url_for('index'))
    return render_template('student.html')

@app.route('/teacher')
def teacher():
    if not session.get('user_logged_in'):
        flash('请先登录')
        return redirect(url_for('index'))
    return render_template('teacher.html')

@app.route('/teacher/login', methods=['POST'])
def teacher_login():
    password = request.form.get('password')
    if password == TEACHER_PASSWORD:
        session['teacher_logged_in'] = True
        return redirect(url_for('teacher_dashboard'))
    else:
        flash('密码错误')
        return redirect(url_for('teacher'))

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if not session.get('teacher_logged_in'):
        return redirect(url_for('teacher'))
    
    questions = get_questions()
    
    if os.path.exists(RECORDS_FILE):
        with open(RECORDS_FILE, 'r', encoding='utf-8') as f:
            records = json.load(f)
    else:
        records = []
    
    return render_template('teacher_dashboard.html', questions=questions, records=records)

@app.route('/teacher/add_question', methods=['POST'])
def add_question():
    if not session.get('teacher_logged_in'):
        return redirect(url_for('teacher'))
    
    question_content = request.form.get('question_content')
    question_image = request.files.get('question_image')
    question_video = request.files.get('question_video')  # 新增视频文件处理
    
    question_id = get_next_question_id()
    question_file = f'question_{question_id}.txt'
    
    with open(os.path.join(QUESTION_FOLDER, question_file), 'w', encoding='utf-8') as f:
        f.write(question_content)
    
    # 处理图片上传
    if question_image and question_image.filename:
        image_path = os.path.join(IMAGE_FOLDER, f'question_{question_id}.png')
        question_image.save(image_path)
    
    # 处理视频上传
    if question_video and question_video.filename:
        # 获取文件扩展名
        file_ext = os.path.splitext(question_video.filename)[1].lower()
        if file_ext in ['.mp4', '.webm', '.ogg']:  # 支持的视频格式
            video_path = os.path.join(VIDEO_FOLDER, f'question_{question_id}{file_ext}')
            question_video.save(video_path)
    
    flash('题目添加成功')
    return redirect(url_for('teacher_dashboard'))

@app.route('/quiz/<student_type>')
def quiz(student_type):
    questions = get_questions()
    
    if not questions:
        flash('目前没有题目可以答题')
        return redirect(url_for('student'))
    
    # 随机选择10道题目
    if len(questions) > 10:
        selected_questions = random.sample(questions, 10)
    else:
        selected_questions = questions
    
    session['quiz_questions'] = selected_questions
    session['student_type'] = student_type
    
    return render_template('quiz.html', questions=selected_questions, student_type=student_type)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    questions = session.get('quiz_questions')
    student_type = session.get('student_type')
    
    if not questions or not student_type:
        return redirect(url_for('student'))
    
    answers = {}
    score = 0
    
    for question in questions:
        question_id = question['id']
        answer = request.form.get(f'answer_{question_id}')
        answers[question_id] = answer
    
    save_record(student_type, questions, answers, score)
    
    return render_template('result.html', questions=questions, answers=answers, score=score)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/chat', methods=['POST'])
def chat():
    def generate():
        # 模拟流式响应
        yield "data: 这是第一条回复\n\n"
        yield "data: 这是第二条回复\n\n"
    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    app.run(debug=True)