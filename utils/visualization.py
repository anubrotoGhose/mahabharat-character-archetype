import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict

def create_radar_chart(quality_ratings: dict, character_name: str):
    """Create radar chart for quality ratings"""
    
    if not quality_ratings:
        # Return empty figure if no data
        fig = go.Figure()
        fig.update_layout(title="No quality ratings available")
        return fig
    
    categories = list(quality_ratings.keys())
    values = list(quality_ratings.values())
    
    # Close the radar chart (connect last point to first)
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill='toself',
        name=character_name,
        line=dict(color='rgb(102, 126, 234)', width=2),
        fillcolor='rgba(102, 126, 234, 0.3)',
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickmode='linear',
                tick0=0,
                dtick=2,
                gridcolor='lightgray'
            ),
            angularaxis=dict(
                gridcolor='lightgray'
            )
        ),
        showlegend=True,
        title=dict(
            text=f"{character_name} - Quality Ratings",
            font=dict(size=18, color='#667eea')
        ),
        height=500,
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    return fig

def create_bar_chart(responses: List[Dict]):
    """Create bar chart comparing overall ratings across characters"""
    
    if not responses:
        fig = go.Figure()
        fig.update_layout(title="No data available")
        return fig
    
    characters = [r['character_name'] for r in responses]
    ratings = [r['analysis']['overall_rating'] for r in responses]
    
    # Create color gradient based on ratings
    colors = ['#667eea' if r >= 7 else '#ffc107' if r >= 5 else '#dc3545' for r in ratings]
    
    fig = go.Figure(data=[
        go.Bar(
            x=characters,
            y=ratings,
            marker=dict(
                color=colors,
                line=dict(color='rgb(8,48,107)', width=1.5)
            ),
            text=[f"{r:.1f}" for r in ratings],
            textposition='outside',
            textfont=dict(size=14, color='black'),
            hovertemplate='<b>%{x}</b><br>Rating: %{y:.1f}/10<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=dict(
            text="Overall Character Ratings Comparison",
            font=dict(size=20, color='#667eea')
        ),
        xaxis_title="Character",
        yaxis_title="Rating (out of 10)",
        yaxis=dict(
            range=[0, 11],
            tickmode='linear',
            tick0=0,
            dtick=2
        ),
        height=450,
        showlegend=False,
        paper_bgcolor='white',
        plot_bgcolor='rgba(240, 242, 246, 0.5)',
        font=dict(size=12),
        hoverlabel=dict(
            bgcolor="white",
            font_size=14
        )
    )
    
    return fig

def create_comparison_chart(responses: List[Dict]):
    """Create comparison chart of average quality ratings across all characters"""
    
    if not responses:
        fig = go.Figure()
        fig.update_layout(title="No data available")
        return fig
    
    # Aggregate quality ratings across all characters
    all_qualities = {}
    
    for response in responses:
        for quality, rating in response['analysis'].get('quality_ratings', {}).items():
            if quality not in all_qualities:
                all_qualities[quality] = []
            all_qualities[quality].append(rating)
    
    if not all_qualities:
        fig = go.Figure()
        fig.update_layout(title="No quality ratings available")
        return fig
    
    # Calculate average ratings
    avg_qualities = {k: sum(v)/len(v) for k, v in all_qualities.items()}
    
    # Sort by rating (descending)
    sorted_qualities = dict(sorted(avg_qualities.items(), key=lambda x: x[1], reverse=True))
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(sorted_qualities.keys()),
            y=list(sorted_qualities.values()),
            marker=dict(
                color=list(sorted_qualities.values()),
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Rating"),
                line=dict(color='rgb(8,48,107)', width=1.5)
            ),
            text=[f"{v:.1f}" for v in sorted_qualities.values()],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Avg Rating: %{y:.1f}/10<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=dict(
            text="Average Quality Ratings Across All Characters",
            font=dict(size=20, color='#667eea')
        ),
        xaxis_title="Quality",
        yaxis_title="Average Rating (out of 10)",
        yaxis=dict(
            range=[0, 11],
            tickmode='linear',
            tick0=0,
            dtick=2
        ),
        height=450,
        paper_bgcolor='white',
        plot_bgcolor='rgba(240, 242, 246, 0.5)',
        font=dict(size=12),
        hoverlabel=dict(
            bgcolor="white",
            font_size=14
        )
    )
    
    return fig

def create_multi_character_radar(responses: List[Dict]):
    """Create radar chart comparing multiple characters"""
    
    if not responses:
        fig = go.Figure()
        fig.update_layout(title="No data available")
        return fig
    
    # Find common qualities across all characters
    all_qualities = set()
    for response in responses:
        all_qualities.update(response['analysis'].get('quality_ratings', {}).keys())
    
    if not all_qualities:
        fig = go.Figure()
        fig.update_layout(title="No quality ratings available")
        return fig
    
    common_qualities = sorted(list(all_qualities))
    
    fig = go.Figure()
    
    # Color palette for different characters
    colors = ['rgb(102, 126, 234)', 'rgb(118, 75, 162)', 'rgb(255, 99, 132)', 
              'rgb(54, 162, 235)', 'rgb(255, 206, 86)', 'rgb(75, 192, 192)']
    
    for idx, response in enumerate(responses):
        quality_ratings = response['analysis'].get('quality_ratings', {})
        
        # Get values for common qualities (0 if not present)
        values = [quality_ratings.get(q, 0) for q in common_qualities]
        
        # Close the radar chart
        categories_closed = common_qualities + [common_qualities[0]]
        values_closed = values + [values[0]]
        
        color = colors[idx % len(colors)]
        
        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill='toself',
            name=response['character_name'],
            line=dict(color=color, width=2),
            fillcolor=color.replace('rgb', 'rgba').replace(')', ', 0.2)'),
            marker=dict(size=6)
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickmode='linear',
                tick0=0,
                dtick=2,
                gridcolor='lightgray'
            ),
            angularaxis=dict(
                gridcolor='lightgray'
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.1
        ),
        title=dict(
            text="Multi-Character Quality Comparison",
            font=dict(size=20, color='#667eea')
        ),
        height=550,
        paper_bgcolor='white',
        plot_bgcolor='white'
    )
    
    return fig

def create_strength_weakness_chart(analysis: Dict):
    """Create horizontal bar chart showing strengths vs areas for improvement"""
    
    strengths = analysis.get('strengths', [])
    improvements = analysis.get('areas_for_improvement', [])
    
    if not strengths and not improvements:
        fig = go.Figure()
        fig.update_layout(title="No data available")
        return fig
    
    # Create data
    categories = []
    values = []
    colors = []
    
    for strength in strengths[:5]:  # Limit to 5
        categories.append(strength[:50] + "..." if len(strength) > 50 else strength)
        values.append(1)
        colors.append('#28a745')
    
    for improvement in improvements[:5]:  # Limit to 5
        categories.append(improvement[:50] + "..." if len(improvement) > 50 else improvement)
        values.append(1)
        colors.append('#ffc107')
    
    fig = go.Figure(data=[
        go.Bar(
            y=categories,
            x=values,
            orientation='h',
            marker=dict(color=colors),
            showlegend=False,
            hovertemplate='%{y}<extra></extra>'
        )
    ])
    
    fig.update_layout(
        title=dict(
            text="Strengths vs Areas for Improvement",
            font=dict(size=18, color='#667eea')
        ),
        xaxis=dict(visible=False),
        yaxis=dict(autorange="reversed"),
        height=400,
        paper_bgcolor='white',
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=60, b=20)
    )
    
    return fig

def create_progress_gauge(overall_rating: float):
    """Create a gauge chart for overall rating"""
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=overall_rating,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Overall Rating", 'font': {'size': 24, 'color': '#667eea'}},
        delta={'reference': 5, 'increasing': {'color': "#28a745"}},
        gauge={
            'axis': {'range': [None, 10], 'tickwidth': 1, 'tickcolor': "darkgray"},
            'bar': {'color': "#667eea"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 3], 'color': '#ffebee'},
                {'range': [3, 5], 'color': '#fff3e0'},
                {'range': [5, 7], 'color': '#e8f5e9'},
                {'range': [7, 10], 'color': '#c8e6c9'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 8
            }
        }
    ))
    
    fig.update_layout(
        paper_bgcolor="white",
        height=300,
        font={'color': "darkgray", 'family': "Arial"}
    )
    
    return fig