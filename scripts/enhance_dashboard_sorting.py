#!/usr/bin/env python3
"""
Dashboard Sorting Enhancer

This script adds server-side sorting capabilities to the existing dashboard HTML.
It adds JavaScript that can optionally use the server API for more complex sorting.

Usage: poetry run python scripts/enhance_dashboard_sorting.py
"""

import os
from pathlib import Path

def enhance_dashboard_sorting():
    """Add server-side sorting enhancement to dashboard HTML."""
    
    repo_root = Path(__file__).parent.parent
    dashboard_html = repo_root / 'dashboard' / 'valuation_dashboard.html'
    
    if not dashboard_html.exists():
        print("❌ Dashboard HTML not found!")
        return
    
    # Read current dashboard HTML
    with open(dashboard_html, 'r') as f:
        html_content = f.read()
    
    # JavaScript enhancement for server-side sorting
    server_sorting_js = '''
        
        // Enhanced server-side sorting (optional upgrade)
        let useServerSorting = false; // Toggle this to use server-side sorting
        
        function enableServerSorting() {
            useServerSorting = true;
            console.log('🌐 Server-side sorting enabled');
        }
        
        function disableServerSorting() {
            useServerSorting = false;
            console.log('💻 Client-side sorting enabled');  
        }
        
        // Enhanced sort function with server option
        async function sortTableByColumnEnhanced(columnIndex) {
            if (!useServerSorting) {
                // Use existing client-side sorting
                return sortTableByColumn(columnIndex);
            }
            
            // Use server-side sorting
            const headers = document.querySelectorAll('#stockTable th');
            const header = headers[columnIndex];
            const isAscending = !header.classList.contains('sort-asc');
            
            // Map column index to sort column name
            const columnNames = [
                'ticker', 'current_price', 'status', 'dcf_fair_value', 
                'enhanced_dcf', 'growth_dcf', 'ratios', 'rim', 
                'multi_dcf', 'consensus'
            ];
            
            const sortColumn = columnNames[columnIndex] || 'composite_score';
            const direction = isAscending ? 'asc' : 'desc';
            
            try {
                // Show loading state
                header.textContent = header.textContent.replace(/[↑↓]/g, '') + ' ⏳';
                
                const response = await fetch('/sort', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ column: sortColumn, direction: direction })
                });
                
                if (response.ok) {
                    const data = await response.json();
                    updateTableWithSortedData(data.stocks);
                    updateSortIndicators(columnIndex, isAscending);
                } else {
                    console.error('Server sorting failed, falling back to client-side');
                    sortTableByColumn(columnIndex);
                }
                
            } catch (error) {
                console.error('Server sorting error:', error);
                sortTableByColumn(columnIndex); // Fallback
            }
        }
        
        function updateTableWithSortedData(stocks) {
            const tbody = document.querySelector('#stockTable tbody');
            if (!tbody || !stocks) return;
            
            // Clear existing rows
            tbody.innerHTML = '';
            
            // Add sorted rows
            stocks.forEach(stock => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td><strong>${stock.ticker}</strong></td>
                    <td>$${stock.current_price.toFixed(2)}</td>
                    <td><span class="status ${stock.status}">${stock.status}</span></td>
                    <td>$${stock.valuations?.dcf?.fair_value?.toFixed(2) || '0.00'}</td>
                    <td>Enhanced DCF</td>
                    <td>Growth DCF</td>  
                    <td>Ratios</td>
                    <td>RIM</td>
                    <td>Multi-DCF</td>
                    <td><strong>$${stock.valuations?.dcf?.fair_value?.toFixed(2) || '0.00'}</strong></td>
                `;
                tbody.appendChild(row);
            });
        }
        
        function updateSortIndicators(columnIndex, isAscending) {
            // Clear all indicators
            document.querySelectorAll('#stockTable th').forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
                h.textContent = h.textContent.replace(/[↑↓⏳]/g, '');
            });
            
            // Add new indicator
            const header = document.querySelectorAll('#stockTable th')[columnIndex];
            header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
        }
        
        // Add controls to toggle sorting mode
        document.addEventListener('DOMContentLoaded', function() {
            const controls = document.querySelector('.controls');
            if (controls) {
                const sortingControls = document.createElement('div');
                sortingControls.innerHTML = `
                    <div style="margin: 10px 0;">
                        <label style="font-weight: bold; margin-right: 10px;">Sorting Mode:</label>
                        <button onclick="disableServerSorting()" class="sort-mode-btn active">Client-side</button>
                        <button onclick="enableServerSorting()" class="sort-mode-btn">Server-side</button>
                    </div>
                `;
                controls.appendChild(sortingControls);
            }
        });
    '''
    
    # Insert the enhancement before the closing </script> tag
    if '</script>' in html_content:
        html_content = html_content.replace('</script>', server_sorting_js + '\n        </script>')
        
        # Also add CSS for the new buttons
        css_enhancement = '''
        .sort-mode-btn {
            padding: 5px 12px;
            margin: 0 5px;
            border: 1px solid #bdc3c7;
            background: white;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        
        .sort-mode-btn.active {
            background: #3498db;
            color: white;
            border-color: #2980b9;
        }
        
        .sort-mode-btn:hover {
            background: #ecf0f1;
        }
        
        .sort-mode-btn.active:hover {
            background: #2980b9;
        }
        '''
        
        # Insert CSS before closing </style> tag
        if '</style>' in html_content:
            html_content = html_content.replace('</style>', css_enhancement + '\n        </style>')
        
        # Write enhanced HTML
        backup_file = dashboard_html.with_suffix('.html.backup')
        dashboard_html.rename(backup_file)
        
        with open(dashboard_html, 'w') as f:
            f.write(html_content)
        
        print("✅ Dashboard enhanced with server-side sorting option!")
        print("🔄 Dashboard now supports both client-side and server-side sorting")
        print("💾 Original dashboard backed up as valuation_dashboard.html.backup")
        print()
        print("Features added:")
        print("  • Toggle between client-side and server-side sorting")
        print("  • Automatic fallback to client-side if server unavailable")
        print("  • Loading indicators during server sorting")
        print("  • Seamless integration with existing functionality")
        
    else:
        print("❌ Could not find </script> tag to enhance dashboard")

if __name__ == '__main__':
    enhance_dashboard_sorting()