FROM mcr.microsoft.com/dotnet/sdk:10.0

WORKDIR /app

COPY Api.csproj ./
RUN dotnet restore

COPY . ./

ENV ASPNETCORE_ENVIRONMENT=Development \
    ASPNETCORE_URLS=http://0.0.0.0:5000

EXPOSE 5000

CMD ["dotnet", "run", "--urls", "http://0.0.0.0:5000"]
