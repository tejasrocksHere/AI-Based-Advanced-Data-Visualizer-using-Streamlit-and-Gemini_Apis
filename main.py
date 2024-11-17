import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import io

# Streamlit app configuration
st.set_page_config(page_title="Data Visualizer and Cleaner with AI Dashboard", layout="wide")

# Global variable to store dashboard plots
if "dashboard_plots" not in st.session_state:
    st.session_state["dashboard_plots"] = []

# Navigation
st.sidebar.title("Navigation")
nav_option = st.sidebar.radio("Go to", ["Data Visualization", "Data Cleaning", "Dashboard", "AI-Created Dashboard","About Me"])

# Sidebar for file upload
st.sidebar.header("Upload CSV File")
uploaded_file = st.sidebar.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.sidebar.success("File uploaded successfully!")

    # Navigation: Data Cleaning
    if nav_option == "Data Cleaning":
        st.title("🧹 Data Cleaning")
        st.write("### Data Preview")
        st.dataframe(df.head())

        # Missing value handling
        st.write("### Handle Missing Values")
        missing_action = st.radio("Choose an action", ["None", "Drop rows with missing values", "Fill missing values"])
        if missing_action == "Drop rows with missing values":
            df = df.dropna()
            st.success("Dropped rows with missing values.")
        elif missing_action == "Fill missing values":
            fill_value = st.text_input("Enter a value to fill missing data:")
            if fill_value:
                df = df.fillna(fill_value)
                st.success(f"Missing values filled with '{fill_value}'.")

        # Duplicate removal
        st.write("### Handle Duplicates")
        if st.button("Remove Duplicates"):
            df = df.drop_duplicates()
            st.success("Duplicates removed.")

        # Column renaming
        st.write("### Rename Columns")
        col_to_rename = st.selectbox("Select a column to rename", df.columns)
        new_col_name = st.text_input(f"Enter a new name for column '{col_to_rename}':")
        if st.button("Rename Column"):
            df = df.rename(columns={col_to_rename: new_col_name})
            st.success(f"Renamed column '{col_to_rename}' to '{new_col_name}'.")

        # Save cleaned data
        st.write("### Download Cleaned Data")
        st.download_button(
            label="Download Cleaned Data as CSV",
            data=df.to_csv(index=False),
            file_name="cleaned_data.csv",
            mime="text/csv",
        )

        st.write("### Cleaned Data Preview")
        st.dataframe(df.head())

    # Navigation: Data Visualization
    elif nav_option == "Data Visualization":
        st.title("📊 Data Visualization")
        st.write("### Data Preview")
        st.dataframe(df.head())

        # Plot options
        st.sidebar.header("Plot Options")
        plot_type = st.sidebar.selectbox(
            "Select Plot Type", 
            ["Scatter Plot", "Line Plot", "Bar Plot", "Histogram", "Box Plot", "Heatmap"]
        )
        
        x_axis = st.sidebar.selectbox("Select X-axis", df.columns)
        y_axis = None if plot_type == "Heatmap" else st.sidebar.selectbox("Select Y-axis", df.columns)

        # Optional options for specific plots
        with st.sidebar.expander("Advanced Options"):
            hue_col = st.selectbox("Select Hue (Optional)", [None] + list(df.columns))
            fig_size = st.slider("Figure Size", min_value=4, max_value=15, value=8)

        # Plotting
        st.write("### Plot")
        plt.figure(figsize=(fig_size, fig_size))
        sns.set_theme()

        try:
            if plot_type == "Scatter Plot":
                sns.scatterplot(data=df, x=x_axis, y=y_axis, hue=hue_col)
            elif plot_type == "Line Plot":
                sns.lineplot(data=df, x=x_axis, y=y_axis, hue=hue_col)
            elif plot_type == "Bar Plot":
                sns.barplot(data=df, x=x_axis, y=y_axis, hue=hue_col)
            elif plot_type == "Histogram":
                sns.histplot(data=df, x=x_axis, hue=hue_col, kde=True)
            elif plot_type == "Box Plot":
                sns.boxplot(data=df, x=x_axis, y=y_axis, hue=hue_col)
            elif plot_type == "Heatmap":
                sns.heatmap(df.corr(), annot=True, cmap="coolwarm")

            # Render the plot and save it as a buffer
            plot_buffer = io.BytesIO()
            plt.savefig(plot_buffer, format="png")
            plot_buffer.seek(0)
            st.pyplot(plt.gcf())

            # Button to add plot to the dashboard
            if st.button("Add to Dashboard"):
                st.session_state["dashboard_plots"].append(plot_buffer.getvalue())
                st.success("Plot added to dashboard!")
        except Exception as e:
            st.error(f"Error creating plot: {e}")

    # Navigation: Dashboard
    elif nav_option == "Dashboard":
        st.title("📋 Dashboard")
        if st.session_state["dashboard_plots"]:
            for i, plot in enumerate(st.session_state["dashboard_plots"]):
                st.image(plot, caption=f"Plot {i+1}")
        else:
            st.write("No plots added to the dashboard yet.")

    # Navigation: AI-Created Dashboard
    elif nav_option == "AI-Created Dashboard":
        st.title("🤖 AI-Created Dashboard")

        # Generate plots using Gemini API
        api_key = "AIzaSyCmISOvZIApzENPfnvQFdcVw9pu0uF0peE"
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
        
        # Generate df.info() output as a string
        buffer = io.StringIO()
        df.info(buf=buffer)
        df_info = buffer.getvalue()
        
        prompt = f"""
        Given the following dataset information:

        {df_info}

        Generate Python code for 6 meaningful plots using matplotlib and seaborn based on the dataset. histogram, pie chart , Heatmap , scatter plot, box plot and another meaninfull  Provide only the code, no explanations or comments.
        """

        response = requests.post(
            endpoint,
            headers={"Content-Type": "application/json"},
            json={"contents": [{"parts": [{"text": prompt}]}]},
        )

        if response.status_code == 200:
            st.write("AI-generated code for plots:")
            ai_output = response.json()
            generated_code = ai_output.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
           
            
            # Remove code block markers if present
            if generated_code.startswith("```python"):
                generated_code = generated_code.strip("```python").strip("```")
            if generated_code.endswith("```"):
                generated_code = generated_code[:-3].strip()
            generated_code = generated_code.replace("```python", "").replace("```", "").strip()
            st.code(generated_code, language="python")

            # Execute the generated code to plot graphs
            try:
                # Pass the DataFrame `df` as a global variable for the executed code
                local_vars = {"df": df, "plt": plt, "sns": sns}
                exec(generated_code, {}, local_vars)

                st.success("Plots generated successfully!")
                
                # Display the generated plots
                for fig in plt.get_fignums():
                    st.pyplot(plt.figure(fig))
            except Exception as e:
                st.error(f"Error executing AI-generated code: {e}")
        else:
            st.error("Failed to fetch AI-generated code. Check your API key or request format.")

    # Navigation: About Me
    elif nav_option == "About Me":
        st.title("👤 About Me")
        st.write("""
        Hi! I'm Tejas Mundhe. I am passionate about technology, Web technogies, and AI. I am currently pursuing a Bachelor's degree in Computer Science with a focus on Artificial Intelligence and Machine Learning. 
        I have worked on various projects such as LastBenchMate, a zero-internet solution for visually impaired students to attend lectures remotely. 
        I have a strong background in programming languages like Python, C++, JavaScript, and more. 
        Feel free to explore my work and connect with me for collaborations or discussions!
        """)

        st.write("### Connect with me:")
        st.write("[GitHub](https://github.com/tejasrocksHere) | [LinkedIn](https://www.linkedin.com/in/tejas-mundhe/)")
        st.write("[Projects](https://tejas-mundhe-projects.netlify.app/) |")


else:
    st.sidebar.info("Awaiting CSV file upload.")
    st.write("## Upload a CSV file to get started.")
