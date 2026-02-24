import os
import subprocess

def backup():
    with open('local_backup.json', 'w', encoding='utf-8') as f:
        subprocess.run([
            'python', 'manage.py', 'dumpdata', 
            '--natural-foreign', '--natural-primary', 
            '-e', 'contenttypes', '-e', 'auth.Permission', 
            '--indent', '2'
        ], stdout=f, check=True)

if __name__ == "__main__":
    backup()
