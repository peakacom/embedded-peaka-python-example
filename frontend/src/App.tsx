import {
  Text,
  Button,
  Box,
  TextField,
  Blockquote,
  Heading,
  Table,
} from "@radix-ui/themes";
import { useState } from "react";

const BASE_URL = "http://localhost:3001";

function App() {
  const [step, setStep] = useState(0);
  const [isFetching, setIsFetching] = useState(false);
  const [projectName, setProjectName] = useState("");
  const [projectAPIKey, setProjectAPIKey] = useState("");
  const [catalogName, setCatalogName] = useState("");
  const [schemaName, setSchemaName] = useState("");
  const [tableName, setTableName] = useState("");
  const [result, setResult] = useState<{ [key: string]: unknown }>({});

  return (
    <div className="w-full h-full flex flex-col justify-center items-center mt-96 gap-8">
      <Heading>Welcome to Embedded Peaka Demo Project.</Heading>
      <Blockquote>
        First create a Peaka Project by clicking Create Project button.
      </Blockquote>
      <Button
        disabled={isFetching}
        onClick={async () => {
          setIsFetching(true);
          const response = await fetch(`${BASE_URL}/create-peaka-project`);
          if (response.ok) {
            const respJSON = await response.json();
            setProjectAPIKey(respJSON.projectApiKey);
            setProjectName(respJSON.projectName);
            setStep(1);
            setIsFetching(false);
          }
        }}
      >
        Create Project
      </Button>
      {(step === 1 || step === 2 || step === 3) && (
        <>
          <Blockquote>
            Your project is created with a project name and API Key. Now click
            Connect button to add your catalog on Peaka.
          </Blockquote>
          <div className="flex justify-center items-center gap-4">
            <Box maxWidth="300px">
              <Text>Project Name</Text>
              <TextField.Root size="3" disabled value={projectName} />
            </Box>
            <Box maxWidth="300px">
              <Text>Project API Key</Text>
              <TextField.Root size="3" disabled value={projectAPIKey} />
            </Box>
            <div className="mt-6">
              <Button
                disabled={isFetching}
                onClick={async () => {
                  setIsFetching(true);
                  const data = {
                    apiKey: projectAPIKey,
                  };
                  const response = await fetch(`${BASE_URL}/connect`, {
                    method: "POST",
                    headers: {
                      "Content-Type": "application/json",
                    },
                    body: JSON.stringify(data),
                  });
                  if (response.ok) {
                    const respJSON = await response.json();
                    setTimeout(() => {
                      window.open(respJSON.sessionUrl, "_blank");
                    });

                    setStep(2);
                    setIsFetching(false);
                  }
                }}
              >
                Connect
              </Button>
            </div>
          </div>
        </>
      )}

      {(step === 2 || step === 3) && (
        <>
          <Blockquote>
            Enter catalog name and schema name and click Get Data button.
          </Blockquote>
          <div className="flex justify-center items-center gap-4">
            <Box maxWidth="300px">
              <Text>Catalog Name</Text>
              <TextField.Root
                size="3"
                value={catalogName}
                onChange={(e) => {
                  setCatalogName(e.target.value as string);
                }}
              />
            </Box>
            <Box maxWidth="300px">
              <Text>Schema Name</Text>
              <TextField.Root
                size="3"
                value={schemaName}
                onChange={(e) => {
                  setSchemaName(e.target.value as string);
                }}
              />
            </Box>
            <Box maxWidth="300px">
              <Text>Table Name</Text>
              <TextField.Root
                size="3"
                value={tableName}
                onChange={(e) => {
                  setTableName(e.target.value as string);
                }}
              />
            </Box>
            <div className="mt-6">
              <Button
                disabled={isFetching}
                onClick={async () => {
                  setIsFetching(true);
                  const data = {
                    apiKey: projectAPIKey,
                    catalogName: catalogName,
                    schemaName: schemaName,
                    tableName: tableName,
                  };

                  const response = await fetch(`${BASE_URL}/get-data`, {
                    method: "POST",
                    headers: {
                      "Content-Type": "application/json",
                    },
                    body: JSON.stringify(data),
                  });
                  if (response.ok) {
                    const respJSON = await response.json();
                    setResult(respJSON);
                    setIsFetching(false);
                    setStep(3);
                  }
                }}
              >
                Get Data
              </Button>
            </div>
          </div>
        </>
      )}
      {step === 3 && (
        <>
          <Blockquote>
            Successfully got the data. Showing sample data 1 row and 10 columns.
          </Blockquote>
          <Table.Root>
            <Table.Header>
              <Table.Row>
                {Object.keys(result).map((key) => (
                  <Table.ColumnHeaderCell>{key}</Table.ColumnHeaderCell>
                ))}
              </Table.Row>
            </Table.Header>

            <Table.Body>
              <Table.Row>
                {Object.keys(result).map((key) => (
                  <Table.Cell>{JSON.stringify(result[key])}</Table.Cell>
                ))}
              </Table.Row>
            </Table.Body>
          </Table.Root>
        </>
      )}
    </div>
  );
}

export default App;
