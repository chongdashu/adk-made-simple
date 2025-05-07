"""
Client module for Agent to Agent (A2A) communication following Google ADK standards.
This module provides utilities for agents to communicate with other agents.
"""

import json
from typing import Dict, Any, Optional, List, Union

import aiohttp
import requests
from pydantic import BaseModel

class AgentClient:
    """Client for communicating with other A2A agents."""
    
    def __init__(self, base_url: str):
        """
        Initialize the agent client.
        
        Args:
            base_url: The base URL of the agent to communicate with
        """
        self.base_url = base_url.rstrip('/')
        self._metadata = None
    
    async def get_metadata(self) -> Dict[str, Any]:
        """
        Retrieve agent metadata from the .well-known/agent.json endpoint.
        
        Returns:
            The agent metadata
        """
        if self._metadata is None:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/.well-known/agent.json") as response:
                    if response.status == 200:
                        self._metadata = await response.json()
                    else:
                        raise Exception(f"Failed to retrieve agent metadata: {response.status}")
        return self._metadata
    
    async def run(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None, 
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a request to the agent's /run endpoint.
        
        Args:
            message: The message to process
            context: Additional context for the request
            session_id: Session identifier for stateful interactions
            
        Returns:
            The agent's response
        """
        if context is None:
            context = {}
            
        payload = {
            "message": message,
            "context": context,
            "session_id": session_id
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/run", 
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response_text = await response.text()
                    raise Exception(f"Agent request failed: {response.status} - {response_text}")
    
    async def call_endpoint(
        self, 
        endpoint: str, 
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call a custom endpoint on the agent.
        
        Args:
            endpoint: The endpoint name (without leading slash)
            data: The data to send to the endpoint
            
        Returns:
            The agent's response
        """
        # Verify that the endpoint exists
        metadata = await self.get_metadata()
        if "endpoints" in metadata and endpoint not in metadata["endpoints"]:
            raise ValueError(f"Endpoint '{endpoint}' not available on agent {metadata.get('name', 'unknown')}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/{endpoint}", 
                json=data,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    response_text = await response.text()
                    raise Exception(f"Agent request to {endpoint} failed: {response.status} - {response_text}")

class AgentDiscovery:
    """Utility for discovering available agents."""
    
    def __init__(self, discovery_url: Optional[str] = None):
        """
        Initialize the agent discovery utility.
        
        Args:
            discovery_url: Optional URL for a discovery service
        """
        self.discovery_url = discovery_url
        self._known_agents = {}
    
    def register_agent(self, name: str, url: str) -> None:
        """
        Register an agent for discovery.
        
        Args:
            name: The name of the agent
            url: The URL of the agent
        """
        self._known_agents[name] = url
    
    def get_agent_url(self, name: str) -> str:
        """
        Get the URL for a registered agent.
        
        Args:
            name: The name of the agent
            
        Returns:
            The URL of the agent
            
        Raises:
            ValueError: If the agent is not registered
        """
        if name not in self._known_agents:
            raise ValueError(f"Agent '{name}' not registered for discovery")
        return self._known_agents[name]
    
    def get_agent_client(self, name: str) -> AgentClient:
        """
        Get a client for a registered agent.
        
        Args:
            name: The name of the agent
            
        Returns:
            An AgentClient for the agent
        """
        url = self.get_agent_url(name)
        return AgentClient(url) 