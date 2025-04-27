import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from shiny import App, ui, render, reactive
import plotly.express as px
from pathlib import Path
from shinywidgets import render_widget, output_widget  

def load_data():
    # Load the dataset directly
    df = pd.read_csv("adult.csv")  
    
    df.columns = df.columns.str.strip().str.lower().str.replace('-', '_')
    # Clean missing values
    df = df[~df['workclass'].isin(["?"])]
    df = df[~df['occupation'].isin(["?"])]
    df['native_country'] = df['native_country'].replace("?", "Unknown")
    
    # Create age groups
    bins = [18, 25, 35, 45, 55, 65, 100]
    labels = ['18-25', '26-35', '36-45', '46-55', '56-65', '65+']
    df['age_group'] = pd.cut(df['age'], bins=bins, labels=labels, right=False)
    
    return df

df = load_data()

app_ui = ui.page_navbar(
   
    ui.nav_panel(
        "About",
        ui.layout_sidebar(
            ui.sidebar(
                ui.h4("Quick Filters"),
                ui.input_dark_mode(),
                ui.input_action_button("demo", "Show Demo Filters", class_="btn-primary"),
                width=300
            ),
            ui.card(
                ui.card_header("📊 Income Inequality Explorer"),
                ui.markdown(f"""
                ### Explore Census Data
                This interactive dashboard analyzes factors influencing income levels (≤50K vs >50K) 
                using the **UCI Adult Dataset** with {len(df):,} records.

                #### Key Features:
                - 🔍 Filter by **demographics** (age, gender, race)
                - 🎓 Compare **education levels** and **occupations**
                - 💰 Analyze **financial factors** (capital gains, work hours)
                """),
                ui.accordion(
                    ui.accordion_panel(
                        "About the Data",
                        ui.markdown("""
                        **Source**: Kaggle  
                        **Variables**:  
                        - **Target**: `income` (binary classification)  
                        - **Features**: 14 demographic/financial attributes  
                        - **Time Period**: 1994 US Census data  

                        *Note: All monetary values are adjusted to 1994 dollars.*
                        """)
                    ),
                    ui.accordion_panel(
                        "How to Use",
                        ui.markdown("""
                        1. Use the sidebar filters in each tab to refine data  
                        2. Hover over charts for detailed values  
                        3. Click legend items to toggle categories  
                        4. Download filtered data via the Financial tab  
                        """)
                    ),
                    open=False
                ),
                ui.div(
                    ui.hr(),
                    ui.tags.small("Created with Shiny for Python | Course Project - Data Visualization & Insight", 
                                 style="color: #6c757d;"),
                    style="text-align: center;"
                )
            ),
            ui.output_plot("data_preview_plot")
        )
    ),
  
    ui.nav_panel(
        "Demographics",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_dark_mode(),
                ui.input_select("gender", "Gender", choices=["All", "Male", "Female"]),
                ui.input_slider("age", "Age Range", min=18, max=90, value=[25, 60]),
                ui.input_select("race", "Race", choices=["All"] + sorted(df["race"].unique())),
                width=300
            ),
            ui.output_ui("demographics_plots")
        )
    ),
    ui.nav_panel(
        "Education & Occupation",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_dark_mode(),
                ui.input_select("education", "Education Level", 
                              choices=["All"] + sorted(df["education"].unique())),
                ui.input_select("occupation", "Occupation", 
                              choices=["All"] + sorted(df["occupation"].unique())),
                width=300
            ),
            ui.output_ui("education_plots")
        )
    ),
    ui.nav_panel(
        "Financial Factors",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_dark_mode(),
                ui.input_checkbox("capital_gain", "Show Only People with Capital Gains", False),
                ui.input_slider("hours", "Weekly Hours Worked", min=1, max=99, value=[30, 50]),
                ui.download_button("download_data", "Download Filtered Data"),
                width=300
            ),
            ui.output_ui("financial_plots")
        )
    ),
    title=ui.div(
        ui.img(src="https://shiny.posit.co/py/assets/shiny-logo.png", height="30px"),
        " Income Inequality Explorer",
        style="display: flex; align-items: center; gap: 10px;"
    ),
    footer=ui.div(
        ui.tags.style("""
        .accordion { margin-top: 20px; margin-bottom: 15px; }
        .card { box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
        .btn-primary { background-color: #0062cc; border-color: #005cbf; }
        """),
        "Data Source: UCI Adult Dataset | Created with Shiny for Python"
    ),
    bg="#0062cc",
    inverse=True
)

def server(input, output, session):
    
    @reactive.effect
    @reactive.event(input.demo)
    def _():
        ui.update_slider("age", value=[30, 50])
        ui.update_select("gender", selected="Female")
        ui.update_select("education", selected="Bachelors")
    
    @output
    @render.plot
    def data_preview_plot():
        plt.figure(figsize=(10, 4))
        sns.countplot(data=df, y='occupation', order=df['occupation'].value_counts().index[:8], 
                     hue='income', palette="Set2")
        plt.title("Top 8 Occupations by Income Level")
        plt.xlabel("Count")
        plt.ylabel("")
        plt.legend(title="Income")
        plt.tight_layout()
        return plt.gcf()

    
    @reactive.calc
    def filtered_data():
        data = df.copy()
        
        # Apply filters
        if input.gender() != "All":
            data = data[data['gender'] == input.gender()]
        
        data = data[(data['age'] >= input.age()[0]) & 
                   (data['age'] <= input.age()[1])]
        
        if input.race() != "All":
            data = data[data['race'] == input.race()]
        
        return data

    @output
    @render.ui
    def demographics_plots():
        data = filtered_data()
        if len(data) == 0:
            return ui.h4("No data available for current filters")
            
        return ui.TagList(
            ui.output_plot("income_by_age_gender"),
            output_widget("income_by_race")  
        )

    @output
    @render.plot
    def income_by_age_gender():
        data = filtered_data()
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=data, x='income', y='age', hue='gender', palette="Set2")
        plt.title("Age Distribution by Income and Gender")
        plt.xlabel("Income Category")
        plt.ylabel("Age")
        plt.tight_layout()
        return plt.gcf()

    @output
    @render_widget  
    def income_by_race():
        data = filtered_data()
        fig = px.sunburst(
            data, 
            path=['race', 'income'], 
            title="Income Distribution by Race",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig.update_traces(textinfo="label+percent parent")
        return fig

    @output
    @render.ui
    def education_plots():
        data = filtered_data()
        if len(data) == 0:
            return ui.h4("No data available for current filters")
            
        return ui.TagList(
            output_widget("income_by_education"),  
            ui.output_plot("top_occupations")
        )

    @output
    @render_widget  
    def income_by_education():
        data = filtered_data()
        if input.education() != "All":
            data = data[data['education'] == input.education()]
        fig = px.histogram(
            data, 
            x='education', 
            color='income', 
            barmode='group',
            title="Income Distribution by Education Level",
            labels={'education': 'Education Level', 'count': 'Count'},
            color_discrete_map={"<=50K": "blue", ">50K": "orange"}
        )
        fig.update_layout(xaxis={'categoryorder':'total descending'})
        return fig

    @output
    @render.plot
    def top_occupations():
        data = filtered_data()
        if input.occupation() != "All":
            data = data[data['occupation'] == input.occupation()]
            
        top_jobs = data[data['income'] == '>50K']['occupation'].value_counts().head(10)
        if len(top_jobs) == 0:
            plt.figure(figsize=(10, 2))
            plt.text(0.5, 0.5, "No data available", ha='center', va='center')
            plt.axis('off')
            return plt.gcf()
            
        plt.figure(figsize=(10, 6))
        sns.barplot(x=top_jobs.values, y=top_jobs.index, palette="viridis")
        plt.title("Top 10 Highest Paying Occupations")
        plt.xlabel("Count")
        plt.ylabel("Occupation")
        plt.tight_layout()
        return plt.gcf()

    @output
    @render.ui
    def financial_plots():
        data = filtered_data()
        if len(data) == 0:
            return ui.h4("No data available for current filters")
            
        return ui.TagList(
            output_widget("capital_gain_plot"),  
            output_widget("hours_vs_income")  
        )

    @output
    @render_widget  
    def capital_gain_plot():
        data = filtered_data()
        if input.capital_gain():
            data = data[data['capital_gain'] > 0]
        fig = px.histogram(
            data, 
            x='capital_gain', 
            color='income',
            title="Capital Gains Distribution",
            nbins=50,
            log_x=True,
            labels={'capital_gain': 'Capital Gains ($)'}
        )
        return fig

    @output
    @render_widget  
    def hours_vs_income():
        data = filtered_data()
        data = data[(data['hours_per_week'] >= input.hours()[0]) & 
                   (data['hours_per_week'] <= input.hours()[1])]
        fig = px.box(
            data, 
            x='income', 
            y='hours_per_week', 
            title="Weekly Hours Worked by Income",
            points="outliers",
            color='income',
            color_discrete_map={"<=50K": "blue", ">50K": "orange"}
        )
        fig.update_yaxes(title_text="Hours per Week")
        return fig

    @output
    @render.download(filename="filtered_data.csv")
    def download_data():
        return filtered_data().to_csv(index=False)

# Run the app
app = App(app_ui, server)