#!/usr/bin/env python3
"""
Simple Dashboard Launcher

This script gives you different ways to access the investment dashboard:

1. View existing dashboard (instant)
2. Update with fresh data and view (takes time but fresh)
3. Run live server with update capability

Usage: uv run python scripts/run_dashboard.py
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def main():
    print("🚀 Investment Dashboard Launcher")
    print("=" * 50)
    
    # Check paths
    repo_root = Path(__file__).parent.parent
    dashboard_html = repo_root / 'dashboard' / 'valuation_dashboard.html'
    dashboard_data = repo_root / 'dashboard' / 'dashboard_data.json'
    
    print(f"📁 Dashboard HTML: {'✅ Exists' if dashboard_html.exists() else '❌ Missing'}")
    print(f"📊 Dashboard Data: {'✅ Exists' if dashboard_data.exists() else '❌ Missing'}")
    print()
    
    print("Choose how to access your dashboard:")
    print()
    print("1. 📖 View Existing Dashboard (instant)")
    print("   → Opens current dashboard HTML in browser")
    print()
    print("2. 🔄 Update & View Dashboard (2-3 minutes)")
    print("   → Runs fresh analysis on your watchlist, then opens dashboard")  
    print()
    print("3. 🌐 Start Live Dashboard Server")
    print("   → Runs interactive server on localhost:8080")
    print()
    print("4. ⚙️  Create Dashboard with Custom Config")
    print("   → Choose a config file and generate dashboard")
    print()
    
    while True:
        choice = input("Enter choice (1-4) or 'q' to quit: ").strip().lower()
        
        if choice == 'q':
            print("👋 Goodbye!")
            return
            
        elif choice == '1':
            if dashboard_html.exists():
                print("🌐 Opening existing dashboard in browser...")
                webbrowser.open(f'file://{dashboard_html.absolute()}')
                print("✅ Dashboard opened!")
            else:
                print("❌ No existing dashboard found. Try option 2 or 4 first.")
            return
            
        elif choice == '2':
            print("🔄 Generating fresh dashboard data...")
            print("   Using watchlist configuration...")
            
            # Run systematic analysis on watchlist
            config_path = repo_root / 'configs' / 'watchlist_analysis.yaml'
            if not config_path.exists():
                config_path = repo_root / 'configs' / 'simple_mixed.yaml'
            
            cmd = ['uv', 'run', 'python', 'scripts/systematic_analysis.py', str(config_path)]
            
            try:
                result = subprocess.run(cmd, cwd=repo_root, check=True, capture_output=True, text=True)
                print("✅ Analysis complete!")
                
                if dashboard_html.exists():
                    print("🌐 Opening updated dashboard...")
                    webbrowser.open(f'file://{dashboard_html.absolute()}')
                    print("✅ Dashboard opened with fresh data!")
                else:
                    print("❌ Dashboard HTML not generated. Check the analysis output.")
                    
            except subprocess.CalledProcessError as e:
                print(f"❌ Analysis failed: {e}")
                print("   Try running manually: uv run python scripts/systematic_analysis.py configs/simple_mixed.yaml")
            return
            
        elif choice == '3':
            print("🌐 Starting dashboard server...")
            print("   This will open http://localhost:8080 in your browser")
            print("   Press Ctrl+C to stop the server")
            
            cmd = ['uv', 'run', 'python', 'scripts/dashboard_server.py']
            
            try:
                subprocess.run(cmd, cwd=repo_root)
            except KeyboardInterrupt:
                print("\n👋 Server stopped")
            return
            
        elif choice == '4':
            print("⚙️ Available configurations:")
            
            configs_dir = repo_root / 'configs'
            config_files = list(configs_dir.glob('*.yaml'))
            
            for i, config_file in enumerate(sorted(config_files), 1):
                print(f"   {i:2d}. {config_file.name}")
            
            print()
            config_choice = input(f"Enter config number (1-{len(config_files)}) or press Enter for watchlist: ").strip()
            
            if config_choice == '':
                chosen_config = 'watchlist_analysis.yaml'
            else:
                try:
                    idx = int(config_choice) - 1
                    if 0 <= idx < len(config_files):
                        chosen_config = sorted(config_files)[idx].name
                    else:
                        print("❌ Invalid choice")
                        continue
                except ValueError:
                    print("❌ Please enter a number")
                    continue
            
            config_path = configs_dir / chosen_config
            
            print(f"🔄 Running analysis with {chosen_config}...")
            cmd = ['uv', 'run', 'python', 'scripts/systematic_analysis.py', str(config_path)]
            
            try:
                result = subprocess.run(cmd, cwd=repo_root, check=True)
                print("✅ Analysis complete!")
                
                if dashboard_html.exists():
                    print("🌐 Opening dashboard...")
                    webbrowser.open(f'file://{dashboard_html.absolute()}')
                    print("✅ Dashboard opened!")
                    
            except subprocess.CalledProcessError as e:
                print(f"❌ Analysis failed: {e}")
            return
            
        else:
            print("❌ Please enter 1, 2, 3, 4, or 'q'")


if __name__ == '__main__':
    main()